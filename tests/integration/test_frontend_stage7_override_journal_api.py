from __future__ import annotations

from fastapi.testclient import TestClient

from tests.integration.test_frontend_stage4_operating_loop_api import make_client
from tests.conftest import seed_account, seed_instrument


def protected_counts(db) -> dict[str, int]:
    return {
        table: int(db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"])
        for table in ("order_tickets", "manual_execution_logs", "transactions", "override_tickets", "decision_journal", "postmortem_tasks")
    }


def declare_payload(account_id: int, instrument_id: int) -> dict:
    return {
        "override_type": "panic",
        "account_id": account_id,
        "instrument_id": instrument_id,
        "side": "sell",
        "requested_quantity": "1",
        "currency": "USD",
        "human_reason": "Stage 7 explicit override test",
        "emotional_state": "stressed but deliberate",
    }


def declare_override(client: TestClient, account_id: int, instrument_id: int) -> dict:
    response = client.post("/api/v1/overrides", json=declare_payload(account_id, instrument_id))
    assert response.status_code == 201, response.text
    return response.json()


def test_override_declaration_creates_journal_and_postmortem_without_official_ticket(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    before = protected_counts(db)
    with make_client(db) as client:
        body = declare_override(client, account_id, instrument_id)

        override = body["override"]
        assert override["status"] == "risk_warned"
        assert override["override_type"] == "panic"
        assert override["human_reason"] == "Stage 7 explicit override test"
        assert override["linked_postmortem_task_id"] is not None
        assert "not an official risk-validated ticket" in override["risk_warning"]
        assert body["linked_journal_entries"][0]["decision_type"] == "override_declared"
        assert body["postmortem_task"]["status"] == "scheduled"
        assert body["postmortem_task"]["override_ticket_id"] == override["override_id"]

        after = protected_counts(db)
        assert after["override_tickets"] == before["override_tickets"] + 1
        assert after["decision_journal"] == before["decision_journal"] + 1
        assert after["postmortem_tasks"] == before["postmortem_tasks"] + 1
        assert after["order_tickets"] == before["order_tickets"]
        assert after["manual_execution_logs"] == before["manual_execution_logs"]
        assert after["transactions"] == before["transactions"]


def test_override_declaration_requires_human_reason(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    payload = declare_payload(account_id, instrument_id)
    payload["human_reason"] = "   "
    with make_client(db) as client:
        response = client.post("/api/v1/overrides", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "human_reason_required"


def test_confirm_and_cancel_override_write_audit_but_do_not_execute(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    with make_client(db) as client:
        declared = declare_override(client, account_id, instrument_id)["override"]
        before_confirm = protected_counts(db)

        confirmed = client.post(f"/api/v1/overrides/{declared['override_id']}/confirm", json={"emotional_state": "calm"})
        assert confirmed.status_code == 200, confirmed.text
        confirm_body = confirmed.json()
        assert confirm_body["override"]["status"] == "human_confirmed"
        assert confirm_body["override"]["human_final_choice"] == "execute"
        assert "confirm_override" not in confirm_body["override"]["available_actions"]

        after_confirm = protected_counts(db)
        assert after_confirm["decision_journal"] == before_confirm["decision_journal"] + 1
        assert after_confirm["manual_execution_logs"] == before_confirm["manual_execution_logs"]
        assert after_confirm["transactions"] == before_confirm["transactions"]
        assert after_confirm["order_tickets"] == before_confirm["order_tickets"]

        cancelled = client.post(f"/api/v1/overrides/{declared['override_id']}/cancel", json={})
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["override"]["status"] == "cancelled"


def test_journal_and_postmortem_lists_return_typed_parsed_entries(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    with make_client(db) as client:
        declared = declare_override(client, account_id, instrument_id)["override"]

        journal = client.get(f"/api/v1/journal?linked_override_id={declared['override_id']}")
        assert journal.status_code == 200
        entries = journal.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["context"] == {}
        detail = client.get(f"/api/v1/journal/{entries[0]['decision_id']}")
        assert detail.status_code == 200
        assert detail.json()["override_ticket_id"] == declared["override_id"]

        postmortems = client.get(f"/api/v1/postmortems?linked_override_id={declared['override_id']}")
        assert postmortems.status_code == 200
        tasks = postmortems.json()["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["prompt_questions"]
        assert tasks[0]["available_actions"] == ["review_task"]


def test_missing_override_and_journal_return_structured_errors(db) -> None:
    with make_client(db) as client:
        override = client.get("/api/v1/overrides/999999")
        assert override.status_code == 404
        assert override.json()["error"]["code"] == "override_not_found"
        journal = client.get("/api/v1/journal/999999")
        assert journal.status_code == 404
        assert journal.json()["error"]["code"] == "journal_entry_not_found"
