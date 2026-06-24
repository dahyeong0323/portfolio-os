from __future__ import annotations

from datetime import date

import pytest

from portfolio_os.execution import ManualExecutionRepository
from portfolio_os.models import ReconciliationResult
from portfolio_os.reconciliation import DEFAULT_TOLERANCE
from portfolio_os.repositories import ReconciliationRepository, TransactionRepository
from portfolio_os.tickets import OrderTicketRepository
from portfolio_os.validators import utc_now
from tests.integration.test_frontend_stage5_manual_execution_api import create_validated_ticket
from tests.integration.test_frontend_stage4_operating_loop_api import make_client, seed_operating_loop


def save_reconciliation(db, account_id: int, as_of: date, status: str) -> int:
    now = utc_now()
    result = ReconciliationResult(
        None,
        account_id,
        as_of,
        now,
        now,
        "provisional",
        "reconciled" if status == "passed" else "broken" if status == "failed" else "provisional",
        status,
        "manual",
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        DEFAULT_TOLERANCE,
        None if status == "passed" else f"{status} test evidence",
    )
    saved = ReconciliationRepository(db).save_reconciliation_result(result)
    return saved.reconciliation_id


def log_pending_execution(client, ticket_id: int, *, executed_at: str = "2026-01-02T10:00:00Z") -> dict:
    response = client.post(
        "/api/v1/executions",
        json={
            "ticket_id": ticket_id,
            "filled_quantity": "1",
            "fill_price": "100",
            "fee": "0",
            "tax": "0",
            "executed_at": executed_at,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_approved_ticket(client, account_id: int, instrument_id: int) -> dict:
    ticket = create_validated_ticket(client, account_id, instrument_id)
    approval = client.post(f"/api/v1/tickets/{ticket['order_ticket_id']}/approve", json={"approval_note": "stage 6"})
    assert approval.status_code == 200, approval.text
    return ticket


def protected_counts(db) -> dict[str, int]:
    return {
        table: int(db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"])
        for table in ("manual_execution_logs", "override_tickets", "reconciliation_snapshots", "transactions")
    }


def test_confirm_after_passed_reconciliation_confirms_only_confirmed_linked_execution(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket_one = create_approved_ticket(client, account_id, instrument_id)
        ticket_two = create_approved_ticket(client, account_id, instrument_id)
        execution_one = log_pending_execution(client, ticket_one["order_ticket_id"])
        execution_two = log_pending_execution(client, ticket_two["order_ticket_id"])
        TransactionRepository(db).mark_transactions_confirmed([execution_one["created_transaction_id"]])
        reconciliation_id = save_reconciliation(db, account_id, date(2026, 1, 2), "passed")
        before = protected_counts(db)

        response = client.post(
            "/api/v1/executions/confirm-after-reconciliation",
            json={
                "reconciliation_id": reconciliation_id,
                "execution_ids": [execution_one["execution_id"], execution_two["execution_id"]],
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["reconciliation_id_used"] == reconciliation_id
        assert body["total_pending_checked"] == 2
        assert body["confirmed_execution_ids"] == [execution_one["execution_id"]]
        assert body["still_pending_execution_ids"] == [execution_two["execution_id"]]
        assert body["skipped_executions"][0]["reason"] == "transaction_not_confirmed"
        assert ManualExecutionRepository(db).get(execution_one["execution_id"]).execution_status == "reconciled"
        assert ManualExecutionRepository(db).get(execution_two["execution_id"]).execution_status == "pending_reconciliation"
        assert OrderTicketRepository(db).get(ticket_one["order_ticket_id"]).status == "reconciled"
        assert OrderTicketRepository(db).get(ticket_two["order_ticket_id"]).status == "executed_provisional"
        after = protected_counts(db)
        assert after["transactions"] == before["transactions"]
        assert after["reconciliation_snapshots"] == before["reconciliation_snapshots"]
        assert after["override_tickets"] == before["override_tickets"]


@pytest.mark.parametrize("status", ["failed", "needs_review"])
def test_failed_or_needs_review_reconciliation_does_not_confirm(db, status: str) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_approved_ticket(client, account_id, instrument_id)
        execution = log_pending_execution(client, ticket["order_ticket_id"])
        TransactionRepository(db).mark_transactions_confirmed([execution["created_transaction_id"]])
        reconciliation_id = save_reconciliation(db, account_id, date(2026, 1, 2), status)

        response = client.post(
            "/api/v1/executions/confirm-after-reconciliation",
            json={"reconciliation_id": reconciliation_id, "execution_ids": [execution["execution_id"]]},
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "confirmation_blocked"
        assert ManualExecutionRepository(db).get(execution["execution_id"]).execution_status == "pending_reconciliation"


def test_execution_without_confirmed_transaction_remains_pending_and_reports_readiness(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_approved_ticket(client, account_id, instrument_id)
        execution = log_pending_execution(client, ticket["order_ticket_id"])
        save_reconciliation(db, account_id, date(2026, 1, 2), "passed")

        pending = client.get("/api/v1/executions/pending")

        assert pending.status_code == 200
        row = pending.json()["executions"][0]
        assert row["manual_execution_id"] == execution["execution_id"]
        assert row["transaction_is_confirmed"] is False
        assert row["confirmation_eligible"] is False
        assert row["confirmation_blocked_reason"] == "transaction_not_confirmed"
        assert row["available_actions"] == ["await_reconciliation"]


def test_execution_ids_scope_prevents_unrelated_confirmation(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket_one = create_approved_ticket(client, account_id, instrument_id)
        ticket_two = create_approved_ticket(client, account_id, instrument_id)
        execution_one = log_pending_execution(client, ticket_one["order_ticket_id"])
        execution_two = log_pending_execution(client, ticket_two["order_ticket_id"])
        TransactionRepository(db).mark_transactions_confirmed(
            [execution_one["created_transaction_id"], execution_two["created_transaction_id"]]
        )
        reconciliation_id = save_reconciliation(db, account_id, date(2026, 1, 2), "passed")

        response = client.post(
            "/api/v1/executions/confirm-after-reconciliation",
            json={"reconciliation_id": reconciliation_id, "execution_ids": [execution_one["execution_id"]]},
        )

        assert response.status_code == 200
        assert response.json()["confirmed_execution_ids"] == [execution_one["execution_id"]]
        assert ManualExecutionRepository(db).get(execution_two["execution_id"]).execution_status == "pending_reconciliation"


def test_future_dated_execution_is_not_confirmed_by_older_reconciliation(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_approved_ticket(client, account_id, instrument_id)
        execution = log_pending_execution(client, ticket["order_ticket_id"], executed_at="2026-01-03T10:00:00Z")
        TransactionRepository(db).mark_transactions_confirmed([execution["created_transaction_id"]])
        reconciliation_id = save_reconciliation(db, account_id, date(2026, 1, 2), "passed")

        response = client.post(
            "/api/v1/executions/confirm-after-reconciliation",
            json={"reconciliation_id": reconciliation_id, "execution_ids": [execution["execution_id"]]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["confirmed_execution_ids"] == []
        assert body["skipped_executions"][0]["reason"] == "execution_after_reconciliation"
        assert ManualExecutionRepository(db).get(execution["execution_id"]).execution_status == "pending_reconciliation"


def test_unscoped_confirmation_request_is_rejected(db) -> None:
    account_id, instrument_id = seed_operating_loop(db)
    with make_client(db) as client:
        ticket = create_approved_ticket(client, account_id, instrument_id)
        log_pending_execution(client, ticket["order_ticket_id"])
        response = client.post("/api/v1/executions/confirm-after-reconciliation", json={})
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "confirmation_blocked"
