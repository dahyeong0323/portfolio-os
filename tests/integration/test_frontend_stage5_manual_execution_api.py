from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from portfolio_os.execution import ManualExecutionRepository
from portfolio_os.repositories import TransactionRepository
from portfolio_os.tickets import OrderTicketRepository
from portfolio_os.validators import utc_now
from tests.integration.test_frontend_stage4_operating_loop_api import (
    create_intent,
    make_client,
    seed_operating_loop,
    validation_payload,
)


def create_validated_ticket(client: TestClient, account_id: int, instrument_id: int) -> dict:
    intent = create_intent(client, account_id, instrument_id)
    validation_response = client.post(f"/api/v1/intents/{intent['intent_id']}/validate", json=validation_payload())
    assert validation_response.status_code == 200, validation_response.text
    validation_id = validation_response.json()["validation"]["risk_validation_id"]
    ticket_response = client.post("/api/v1/tickets", json={"risk_validation_id": validation_id})
    assert ticket_response.status_code == 201, ticket_response.text
    return ticket_response.json()["ticket"]


def protected_counts(db) -> dict[str, int]:
    return {
        table: int(db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"])
        for table in ("manual_execution_logs", "override_tickets", "reconciliation_snapshots", "transactions")
    }


def test_approve_ticket_writes_audit_but_does_not_execute(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_validated_ticket(client, account_id, instrument_id)
        before = protected_counts(db)

        response = client.post(
            f"/api/v1/tickets/{ticket['order_ticket_id']}/approve",
            json={"approval_note": "human reviewed in Stage 5", "emotional_state": "calm"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["new_ticket_status"] == "approved"
        assert body["linked_decision_journal_entry_id"] is not None
        assert body["available_actions"] == ["log_manual_execution"]
        assert "manual_execution_logged" not in [event["event_type"] for event in body["ticket_events"]]
        after = protected_counts(db)
        assert after["manual_execution_logs"] == before["manual_execution_logs"]
        assert after["transactions"] == before["transactions"]
        assert after["override_tickets"] == before["override_tickets"]
        assert after["reconciliation_snapshots"] == before["reconciliation_snapshots"]


def test_approve_invalid_or_expired_ticket_returns_structured_error(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_validated_ticket(client, account_id, instrument_id)
        first = client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "ok"})
        assert first.status_code == 200
        second = client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "again"})
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "ticket_invalid_state"

        expired = create_validated_ticket(client, account_id, instrument_id)
        db.execute(
            "UPDATE order_tickets SET expires_at = ? WHERE order_ticket_id = ?",
            ((utc_now() - timedelta(days=1)).isoformat().replace("+00:00", "Z"), expired["order_ticket_id"]),
        )
        db.commit()
        expired_response = client.post(f"/api/v1/tickets/{expired['order_ticket_id']}/approve", json={"approval_note": "late"})
        assert expired_response.status_code == 409
        assert expired_response.json()["error"]["code"] == "ticket_expired"


def test_reject_ticket_writes_audit_and_blocks_later_approval(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_validated_ticket(client, account_id, instrument_id)
        missing_reason = client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/reject", json={})
        assert missing_reason.status_code == 422
        assert missing_reason.json()["error"]["code"] == "rejection_reason_required"

        response = client.post(
            f"/api/v1/tickets/{ticket['order_ticket_id']}/reject",
            json={"rejection_reason": "risk note changed", "emotional_state": "patient"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["new_ticket_status"] == "rejected"
        assert body["linked_decision_journal_entry_id"] is not None
        assert body["available_actions"] == []

        approve = client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "try"})
        assert approve.status_code == 409
        assert approve.json()["error"]["code"] == "ticket_invalid_state"


def test_manual_execution_requires_approved_ticket_and_creates_provisional_transaction(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_validated_ticket(client, account_id, instrument_id)
        blocked = client.post(
            "/api/v1/executions",
            json={
                "ticket_id": ticket["order_ticket_id"],
                "filled_quantity": "1",
                "fill_price": "100",
                "fee": "0.25",
                "tax": "0",
                "executed_at": "2026-01-02T10:00:00Z",
            },
        )
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "manual_execution_blocked"

        client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "ready"})
        before = protected_counts(db)
        response = client.post(
            "/api/v1/executions",
            json={
                "ticket_id": ticket["order_ticket_id"],
                "filled_quantity": "1",
                "fill_price": "100",
                "fee": "0.25",
                "tax": "0",
                "executed_at": "2026-01-02T10:00:00Z",
                "broker_reference": "DEMO-BROKER-REF",
                "notes": "human manually executed outside Portfolio OS",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["execution_status"] == "pending_reconciliation"
        assert body["pending_reconciliation"] is True
        assert body["linked_ticket_id"] == ticket["order_ticket_id"]
        assert body["created_transaction_id"] is not None
        assert body["provisional_transaction"]["is_confirmed"] is False
        assert body["provisional_transaction"]["source"] == "manual"
        assert body["blocked_actions"] == [
            "broker_write_not_available",
            "automatic_execution_not_available",
            "transaction_not_confirmed",
        ]

        updated_ticket = OrderTicketRepository(db).get(ticket["order_ticket_id"])
        assert updated_ticket.status == "executed_provisional"
        execution = ManualExecutionRepository(db).get(body["execution_id"])
        tx = TransactionRepository(db).get_transaction(execution.created_transaction_id)
        assert tx is not None
        assert tx.is_confirmed is False
        after = protected_counts(db)
        assert after["manual_execution_logs"] == before["manual_execution_logs"] + 1
        assert after["transactions"] == before["transactions"] + 1
        assert after["override_tickets"] == before["override_tickets"]
        assert after["reconciliation_snapshots"] == before["reconciliation_snapshots"]


def test_execution_detail_and_pending_include_linked_ticket(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_validated_ticket(client, account_id, instrument_id)
        client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "ready"})
        logged = client.post(
            "/api/v1/executions",
            json={
                "ticket_id": ticket["order_ticket_id"],
                "filled_quantity": "1",
                "fill_price": "100",
                "fee": "0",
                "tax": "0",
                "executed_at": f"{date(2026, 1, 2).isoformat()}T10:00:00Z",
            },
        ).json()

        detail = client.get(f"/api/v1/executions/{logged['execution_id']}")
        assert detail.status_code == 200
        assert detail.json()["linked_ticket"]["order_ticket_id"] == ticket["order_ticket_id"]

        pending = client.get("/api/v1/executions/pending")
        assert pending.status_code == 200
        body = pending.json()
        assert body["count"] == 1
        assert body["executions"][0]["linked_ticket"]["order_ticket_id"] == ticket["order_ticket_id"]
        assert body["executions"][0]["created_transaction_id"] == logged["created_transaction_id"]
