from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portfolio_os.api.app import create_app
from portfolio_os.api.deps import open_read_only_database
from portfolio_os.execution import ManualExecutionService
from portfolio_os.intents import TransactionIntentService
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ExternalCash, ExternalPosition
from portfolio_os.reconciliation import ReconciliationService
from portfolio_os.repositories import (
    AccountRepository,
    CashBalanceRepository,
    InstrumentRepository,
    ReconciliationRepository,
)
from portfolio_os.risk import RiskEngine, seed_default_risk_policy
from portfolio_os.risk.repositories import PricingRepository
from portfolio_os.tickets import OrderTicketService
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_buy, seed_cash_anchor, seed_instrument

API_PATHS = (
    "/api/v1/health",
    "/api/v1/ledger/status",
    "/api/v1/ledger/snapshot",
    "/api/v1/accounts",
    "/api/v1/instruments",
    "/api/v1/reconciliations/latest",
    "/api/v1/tickets",
    "/api/v1/executions/pending",
)


@pytest.fixture
def client(db):
    with TestClient(create_app(db.db_path, app_mode="test-read-only")) as test_client:
        yield test_client


def build_external(account_id: int, instrument_id: int) -> ExternalAccountSnapshot:
    return ExternalAccountSnapshot(
        as_of_date=date(2026, 1, 3),
        source="manual",
        positions=(ExternalPosition(account_id, "AAPL", "USD", Decimal("1"), "NASDAQ", instrument_id),),
        cash=(ExternalCash(account_id, "USD", Decimal("9900")),),
        liabilities=(),
        tax_reserves=(),
        received_at=utc_now(),
    )


def reconcile_cash_account(db, account_id: int) -> None:
    as_of = date(2026, 1, 1)
    ledger = LedgerSnapshotBuilder(db).build_snapshot(as_of, account_id)
    external = ExternalAccountSnapshot(
        as_of_date=as_of,
        source="manual",
        positions=(),
        cash=(ExternalCash(account_id, "USD", Decimal("10000")),),
        liabilities=(),
        tax_reserves=(),
        received_at=utc_now(),
    )
    saved = ReconciliationRepository(db).save_reconciliation_result(
        ReconciliationService().run_reconciliation(ledger, external, account_id=account_id)
    )
    assert saved.reconciliation_status == "passed"
    cash_ids = [item.cash_balance_id for item in CashBalanceRepository(db).list_cash_balances(account_id, as_of)]
    CashBalanceRepository(db).mark_cash_balances_reconciled(cash_ids)


def seed_ticket_and_execution(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    reconcile_cash_account(db, account_id)
    policy_id = seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    intent = TransactionIntentService(db).create_intent(
        account_id,
        instrument_id,
        "buy",
        "USD",
        Decimal("1"),
        None,
        Decimal("100"),
        "API read test",
    )
    validation = RiskEngine(db).validate_and_persist(
        intent,
        LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id),
        policy_id,
        date(2026, 1, 2),
    )
    ticket = OrderTicketService(db).create_ticket_from_validation(
        validation.risk_validation_id,
        utc_now() + timedelta(days=1),
    )
    approved = OrderTicketService(db).approve_ticket(ticket.order_ticket_id, "API read test")
    ManualExecutionService(db).log_execution_for_ticket(
        approved.order_ticket_id,
        Decimal("1"),
        Decimal("100"),
        Decimal("0.25"),
        Decimal("0.10"),
        datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc),
        "TEST-EXECUTION",
    )


def snapshot_database(db) -> dict[str, list[dict[str, object]]]:
    tables = [
        row["name"]
        for row in db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {table: db.fetch_all(f'SELECT * FROM "{table}" ORDER BY rowid') for table in tables}


def test_health_reports_database_and_migration_readiness(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_status"] == "ok"
    assert body["database_reachable"] is True
    assert body["database_ready"] is True
    assert body["app_mode"] == "test-read-only"
    assert body["migrations"]["ready"] is True
    assert body["migrations"]["applied_count"] == body["migrations"]["expected_count"]


def test_empty_state_responses_are_clean(client) -> None:
    status = client.get("/api/v1/ledger/status")
    assert status.status_code == 200
    assert status.json()["ledger_status"] == "provisional"

    snapshot = client.get("/api/v1/ledger/snapshot", params={"as_of_date": "2026-01-01"})
    assert snapshot.status_code == 200
    assert snapshot.json()["positions"] == []
    assert snapshot.json()["cash"] == []

    assert client.get("/api/v1/accounts").json() == {
        "count": 0,
        "active_count": 0,
        "inactive_count": 0,
        "accounts": [],
    }
    assert client.get("/api/v1/instruments").json() == {
        "count": 0,
        "active_count": 0,
        "inactive_count": 0,
        "instruments": [],
    }
    assert client.get("/api/v1/reconciliations/latest").json() == {
        "found": False,
        "reconciliation": None,
    }
    assert client.get("/api/v1/tickets").json() == {"count": 0, "tickets": []}
    assert client.get("/api/v1/executions/pending").json() == {"count": 0, "executions": []}


def test_accounts_and_instruments_include_inactive_records(db, client) -> None:
    active_account_id = seed_account(db)
    inactive_account = AccountRepository(db).create_account("Closed", "Test Bank", "cash", "USD")
    AccountRepository(db).deactivate_account(inactive_account.account_id, date(2026, 1, 31))
    active_instrument_id = seed_instrument(db)
    inactive_instrument = InstrumentRepository(db).create_instrument("OLD", "Old Fund", "fund", "USD")
    db.execute("UPDATE instruments SET is_active = 0 WHERE instrument_id = ?", (inactive_instrument.instrument_id,))
    db.commit()

    accounts = client.get("/api/v1/accounts").json()
    assert accounts["count"] == 2
    assert accounts["active_count"] == 1
    assert {item["account_id"] for item in accounts["accounts"]} == {active_account_id, inactive_account.account_id}

    instruments = client.get("/api/v1/instruments").json()
    assert instruments["count"] == 2
    assert instruments["active_count"] == 1
    assert {item["instrument_id"] for item in instruments["instruments"]} == {
        active_instrument_id,
        inactive_instrument.instrument_id,
    }


def test_ledger_snapshot_uses_domain_builder_and_serializes_decimal_values(db, client) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)

    response = client.get("/api/v1/ledger/snapshot", params={"as_of_date": "2026-01-03"})
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_date"] == "2026-01-03"
    assert body["ledger_status"] == "provisional"
    assert body["positions"][0]["quantity"] == "1"
    assert body["positions"][0]["average_cost"] == "100"
    assert body["cash"][0]["amount"] == "9900"
    assert body["generated_at"].endswith("Z")


def test_latest_reconciliation_decodes_stored_json_into_typed_response(db, client) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)
    ledger = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id)
    saved = ReconciliationRepository(db).save_reconciliation_result(
        ReconciliationService().run_reconciliation(ledger, build_external(account_id, instrument_id), account_id=account_id)
    )

    response = client.get("/api/v1/reconciliations/latest")
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    reconciliation = body["reconciliation"]
    assert reconciliation["reconciliation_id"] == saved.reconciliation_id
    assert reconciliation["reconciliation_status"] == "passed"
    assert reconciliation["expected_positions"][0]["quantity"] == "1"
    assert reconciliation["actual_cash"][0]["amount"] == "9900"
    assert reconciliation["tolerance"]["cash_abs"] == "1.00"
    assert "expected_positions_json" not in reconciliation

    status = client.get("/api/v1/ledger/status").json()
    assert status["last_reconciled_at"] is not None


def test_tickets_and_pending_executions_are_read_only_views(db, client) -> None:
    seed_ticket_and_execution(db)

    tickets = client.get("/api/v1/tickets")
    assert tickets.status_code == 200
    ticket_body = tickets.json()
    assert ticket_body["count"] == 1
    assert ticket_body["tickets"][0]["status"] == "executed_provisional"
    assert ticket_body["tickets"][0]["ticket_notional"] == "100"

    executions = client.get("/api/v1/executions/pending")
    assert executions.status_code == 200
    execution_body = executions.json()
    assert execution_body["count"] == 1
    assert execution_body["executions"][0]["execution_status"] == "pending_reconciliation"
    assert execution_body["executions"][0]["fee_amount"] == "0.25"
    assert execution_body["executions"][0]["broker_execution_ref"] == "TEST-EXECUTION"


def test_missing_and_incomplete_databases_return_safe_errors(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.sqlite3"
    with TestClient(create_app(missing_path)) as missing_client:
        health = missing_client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["database_reachable"] is False
        response = missing_client.get("/api/v1/accounts")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "database_unavailable"
    assert not missing_path.exists()

    incomplete_path = tmp_path / "incomplete.sqlite3"
    sqlite3.connect(incomplete_path).close()
    with TestClient(create_app(incomplete_path)) as incomplete_client:
        health = incomplete_client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["database_reachable"] is True
        assert health.json()["database_ready"] is False
        response = incomplete_client.get("/api/v1/ledger/status")
        assert response.status_code == 503
        assert response.json()["error"] == {
            "code": "database_not_ready",
            "message": "The Portfolio OS database migrations are not ready.",
            "details": None,
        }


def test_invalid_date_uses_structured_validation_error(client) -> None:
    response = client.get("/api/v1/ledger/snapshot", params={"as_of_date": "not-a-date"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "request_validation_error"
    assert body["error"]["details"][0]["location"] == ["query", "as_of_date"]


def test_all_get_endpoints_leave_database_tables_unchanged(db, client) -> None:
    seed_ticket_and_execution(db)
    before = snapshot_database(db)

    for path in API_PATHS:
        response = client.get(path)
        assert response.status_code == 200, response.text

    assert snapshot_database(db) == before


def test_api_database_connection_enforces_query_only(db) -> None:
    before = db.fetch_all("SELECT * FROM accounts")
    with open_read_only_database(db.db_path) as api_db:
        assert api_db.read_only is True
        assert api_db.fetch_one("PRAGMA query_only")["query_only"] == 1
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            api_db.execute(
                "INSERT INTO accounts(account_name, institution_name, account_type, base_currency) VALUES (?, ?, ?, ?)",
                ("Blocked", "Blocked", "cash", "USD"),
            )
    assert db.fetch_all("SELECT * FROM accounts") == before


def test_openapi_preserves_the_frontend_stage1_get_contract(client) -> None:
    schema = client.get("/openapi.json").json()
    assert set(API_PATHS).issubset(schema["paths"])
    assert all("get" in schema["paths"][path] for path in API_PATHS)
