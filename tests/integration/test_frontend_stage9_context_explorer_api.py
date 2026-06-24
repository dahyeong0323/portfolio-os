from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from portfolio_os.api.app import create_app


def make_client(db, tmp_path: Path) -> TestClient:
    report_dir = tmp_path / "exports" / "reconciliation_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return TestClient(create_app(db.db_path, app_mode="test-context-explorer", report_dir=report_dir))


def protected_rows(db) -> dict[str, list[dict]]:
    tables = (
        "transactions",
        "cash_balances",
        "risk_validation_results",
        "order_tickets",
        "manual_execution_logs",
        "override_tickets",
        "decision_journal",
        "research_packets",
        "macro_context_packets",
        "senior_memos",
        "context_packages",
        "governance_audit_events",
    )
    return {table: db.fetch_all(f"SELECT * FROM {table} ORDER BY 1") for table in tables}


def test_context_explorer_lists_return_clean_empty_states(db, tmp_path: Path) -> None:
    with make_client(db, tmp_path) as client:
        research = client.get("/api/v1/research")
        assert research.status_code == 200
        assert research.json() == {"count": 0, "items": []}

        macro = client.get("/api/v1/macro")
        assert macro.status_code == 200
        assert macro.json() == {"count": 0, "items": []}

        memos = client.get("/api/v1/senior-memos")
        assert memos.status_code == 200
        assert memos.json() == {"count": 0, "memos": []}


def test_governance_overview_and_events_return_clean_empty_state(db, tmp_path: Path) -> None:
    with make_client(db, tmp_path) as client:
        overview = client.get("/api/v1/governance")
        assert overview.status_code == 200
        payload = overview.json()
        assert payload["context_package_status"] is None
        assert payload["canary"] is None
        assert payload["health"] is None
        assert payload["available_actions"] == ["view", "open_report"]
        assert "broker_write" in payload["blocked_actions"]

        events = client.get("/api/v1/governance/events")
        assert events.status_code == 200
        assert events.json() == {"count": 0, "events": []}


def test_context_detail_unknown_ids_return_structured_404(db, tmp_path: Path) -> None:
    with make_client(db, tmp_path) as client:
        for path, code in (
            ("/api/v1/research/999", "research_not_found"),
            ("/api/v1/macro/999", "macro_context_not_found"),
            ("/api/v1/senior-memos/999", "senior_memo_not_found"),
        ):
            response = client.get(path)
            assert response.status_code == 404
            assert response.json()["error"]["code"] == code


def test_context_explorer_does_not_mutate_protected_tables_or_expose_paths(db, tmp_path: Path) -> None:
    before = protected_rows(db)
    with make_client(db, tmp_path) as client:
        for path in (
            "/api/v1/research",
            "/api/v1/macro",
            "/api/v1/senior-memos",
            "/api/v1/governance",
            "/api/v1/governance/events",
        ):
            response = client.get(path)
            assert response.status_code == 200
            assert str(tmp_path) not in response.text
            assert "C:\\" not in response.text
    assert protected_rows(db) == before
