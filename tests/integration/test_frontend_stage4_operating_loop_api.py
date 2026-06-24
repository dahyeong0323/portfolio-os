from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from portfolio_os.api.app import create_app
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ExternalCash
from portfolio_os.reconciliation import ReconciliationService
from portfolio_os.repositories import CashBalanceRepository, ReconciliationRepository
from portfolio_os.risk import seed_default_risk_policy
from portfolio_os.risk.repositories import PricingRepository
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_cash_anchor, seed_instrument


def make_client(db) -> TestClient:
    return TestClient(create_app(db.db_path, app_mode="test-operating-loop"))


def reconcile_cash_account(db, account_id: int, amount: str = "10000", as_of: date = date(2026, 1, 1)) -> None:
    ledger = LedgerSnapshotBuilder(db).build_snapshot(as_of, account_id)
    external = ExternalAccountSnapshot(
        as_of_date=as_of,
        source="manual",
        positions=(),
        cash=(ExternalCash(account_id, "USD", Decimal(amount)),),
        liabilities=(),
        tax_reserves=(),
        received_at=utc_now(),
    )
    result = ReconciliationService().run_reconciliation(ledger, external, account_id=account_id)
    saved = ReconciliationRepository(db).save_reconciliation_result(result)
    assert saved.reconciliation_status == "passed"
    cash_ids = [item.cash_balance_id for item in CashBalanceRepository(db).list_cash_balances(account_id, as_of)]
    CashBalanceRepository(db).mark_cash_balances_reconciled(cash_ids)


def seed_operating_loop(db, cash: str = "10000") -> tuple[int, int]:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id, cash, date(2026, 1, 1))
    reconcile_cash_account(db, account_id, cash)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    return account_id, instrument_id


def create_intent(client: TestClient, account_id: int, instrument_id: int, *, notional: str = "500") -> dict:
    response = client.post(
        "/api/v1/intents",
        json={
            "account_id": account_id,
            "instrument_id": instrument_id,
            "side": "buy",
            "currency": "USD",
            "requested_notional": notional,
            "limit_price": "100",
            "rationale": "Stage 4 API test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["intent"]


def validation_payload(as_of_date: str = "2026-01-02") -> dict[str, str]:
    return {"as_of_date": as_of_date}


def protected_rows(db) -> dict[str, list[dict]]:
    return {
        table: db.fetch_all(f"SELECT * FROM {table} ORDER BY 1")
        for table in ("manual_execution_logs", "override_tickets", "reconciliation_snapshots", "transactions")
    }


def test_create_intent_and_validate_passed_then_create_ticket_detail(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    before = protected_rows(db)
    with make_client(db) as client:
        intent = create_intent(client, account_id, instrument_id)
        assert intent["status"] == "drafted"
        assert intent["requested_notional"] == "500"

        validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
        assert validation_response.status_code == 200, validation_response.text
        validation = validation_response.json()["validation"]
        assert validation["validation_status"] == "passed"
        assert validation_response.json()["ledger_status_gate"]["status"] == "passed"
        assert validation_response.json()["next_available_actions"] == ["create_ticket"]

        detail = client.get(f"/api/v1/risk/validations/{validation['risk_validation_id']}")
        assert detail.status_code == 200
        assert detail.json()["associated_intent_id"] == intent["intent_id"]

        ticket_response = client.post("/api/v1/tickets", json={"risk_validation_id": validation["risk_validation_id"]})
        assert ticket_response.status_code == 201, ticket_response.text
        ticket = ticket_response.json()["ticket"]
        assert ticket["status"] == "validated"
        assert ticket_response.json()["available_actions"] == ["approve_ticket", "reject_ticket"]
        assert ticket_response.json()["blocked_actions"] == [
            "modify_deferred",
            "broker_write_not_available",
            "automatic_execution_not_available",
            "manual_execution_requires_approval",
        ]

        ticket_detail = client.get(f"/api/v1/tickets/{ticket['order_ticket_id']}")
        assert ticket_detail.status_code == 200
        body = ticket_detail.json()
        assert body["linked_intent"]["intent_id"] == intent["intent_id"]
        assert body["linked_risk_validation"]["risk_validation_id"] == validation["risk_validation_id"]
        assert body["ticket_events"][0]["event_type"] == "created"

    assert protected_rows(db) == before


def test_intent_validation_errors_are_structured(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        missing_amount = client.post(
            "/api/v1/intents",
            json={"account_id": account_id, "instrument_id": instrument_id, "side": "buy", "currency": "USD"},
        )
        assert missing_amount.status_code == 422
        assert missing_amount.json()["error"]["code"] == "request_validation_error"

        missing_account = client.post(
            "/api/v1/intents",
            json={
                "account_id": 999999,
                "instrument_id": instrument_id,
                "side": "buy",
                "currency": "USD",
                "requested_notional": "100",
            },
        )
        assert missing_account.status_code == 404
        assert missing_account.json()["error"]["code"] == "account_not_found"

        intent = create_intent(client, account_id, instrument_id)
        bad_date = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json={"as_of_date": "bad-date"})
        assert bad_date.status_code == 422
        assert bad_date.json()["error"]["code"] == "invalid_as_of_date"


def test_validate_intent_adjusted_and_ticket_uses_adjusted_notional(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        intent = create_intent(client, account_id, instrument_id, notional="1500")
        validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
        assert validation_response.status_code == 200
        validation = validation_response.json()["validation"]
        assert validation["validation_status"] == "adjusted"
        assert validation["max_allowed_notional"] == "1000"
        assert validation["approved_notional"] == "1000"

        ticket_response = client.post("/api/v1/tickets", json={"risk_validation_id": validation["risk_validation_id"]})
        assert ticket_response.status_code == 201
        assert ticket_response.json()["ticket"]["ticket_notional"] == "1000"


def test_rejected_validation_cannot_create_ticket(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    with make_client(db) as client:
        intent = create_intent(client, account_id, instrument_id)
        validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
        assert validation_response.status_code == 200
        validation = validation_response.json()["validation"]
        assert validation["validation_status"] == "rejected"
        assert validation_response.json()["next_available_actions"] == []

        ticket_response = client.post("/api/v1/tickets", json={"risk_validation_id": validation["risk_validation_id"]})
        assert ticket_response.status_code == 409
        assert ticket_response.json()["error"]["code"] == "risk_validation_rejected"


def test_expired_validation_cannot_create_ticket(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        intent = create_intent(client, account_id, instrument_id)
        validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
        validation_id = validation_response.json()["validation"]["risk_validation_id"]
        db.execute(
            "UPDATE risk_validation_results SET expires_at = ? WHERE risk_validation_id = ?",
            ((utc_now() - timedelta(days=1)).isoformat().replace("+00:00", "Z"), validation_id),
        )
        db.commit()

        ticket_response = client.post("/api/v1/tickets", json={"risk_validation_id": validation_id})
        assert ticket_response.status_code == 409
        assert ticket_response.json()["error"]["code"] == "ticket_create_blocked"


def test_broken_ledger_gate_rejects_risk_increasing_intent(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    with make_client(db) as client:
        intent = create_intent(client, account_id, instrument_id)
        validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
        assert validation_response.status_code == 200
        body = validation_response.json()
        assert body["validation"]["ledger_status_at_validation"] in {"provisional", "broken"}
        assert body["validation"]["validation_status"] == "rejected"
        assert body["ledger_status_gate"]["check_code"] == "LEDGER_STATUS_GATE"
