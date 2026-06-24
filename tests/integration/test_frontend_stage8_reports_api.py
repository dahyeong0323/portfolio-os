from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from portfolio_os.api.app import create_app


def make_client(db, tmp_path: Path) -> TestClient:
    report_dir = tmp_path / "exports" / "reconciliation_reports"
    return TestClient(create_app(db.db_path, app_mode="test-reports", report_dir=report_dir))


def write_reports(tmp_path: Path) -> Path:
    exports = tmp_path / "exports"
    reconciliation = exports / "reconciliation_reports"
    risk = exports / "risk_reports"
    reconciliation.mkdir(parents=True)
    risk.mkdir(parents=True)
    (reconciliation / "reconciliation_7.md").write_text("# Reconciliation Report\n\n- Reconciliation ID: 7\n", encoding="utf-8")
    (reconciliation / "reconciliation_7.json").write_text('{"reconciliation_id":7}', encoding="utf-8")
    (risk / "risk_validation_11.md").write_text("# Risk Validation Report\n\n<script>alert(1)</script>\n", encoding="utf-8")
    (exports / "senior_memos").mkdir(parents=True)
    return reconciliation


def protected_rows(db) -> dict[str, list[dict]]:
    tables = (
        "transactions",
        "cash_balances",
        "risk_validation_results",
        "order_tickets",
        "manual_execution_logs",
        "override_tickets",
        "decision_journal",
    )
    return {table: db.fetch_all(f"SELECT * FROM {table} ORDER BY 1") for table in tables}


def test_report_categories_and_lists_work(db, tmp_path: Path) -> None:
    write_reports(tmp_path)
    with make_client(db, tmp_path) as client:
        categories = client.get("/api/v1/reports/categories")
        assert categories.status_code == 200
        payload = categories.json()["categories"]
        reconciliation = next(item for item in payload if item["category_id"] == "reconciliation")
        assert reconciliation["report_count"] == 2
        assert reconciliation["supported_formats"] == ["markdown", "json"]

        risk = client.get("/api/v1/reports", params={"category": "risk_validation", "format": "markdown"})
        assert risk.status_code == 200
        assert risk.json()["count"] == 1
        assert risk.json()["reports"][0]["linked_object_type"] == "risk_validation"
        assert risk.json()["reports"][0]["linked_object_id"] == "11"
        assert risk.json()["reports"][0]["available_actions"] == ["view", "copy", "download"]


def test_report_detail_download_and_empty_category(db, tmp_path: Path) -> None:
    write_reports(tmp_path)
    with make_client(db, tmp_path) as client:
        listing = client.get("/api/v1/reports", params={"category": "reconciliation", "format": "markdown"}).json()
        reference = listing["reports"][0]["report_reference"]

        detail = client.get(f"/api/v1/reports/{reference}")
        assert detail.status_code == 200
        assert detail.json()["format"] == "markdown"
        assert "Reconciliation ID: 7" in detail.json()["content"]
        assert "path" not in detail.text.lower()

        download = client.get(f"/api/v1/reports/{reference}/download")
        assert download.status_code == 200
        assert "Reconciliation ID: 7" in download.text

        empty = client.get("/api/v1/reports", params={"category": "senior_memo"})
        assert empty.status_code == 200
        assert empty.json() == {"count": 0, "reports": []}


def test_report_errors_block_paths_and_unsupported_formats(db, tmp_path: Path) -> None:
    write_reports(tmp_path)
    with make_client(db, tmp_path) as client:
        missing = client.get("/api/v1/reports/report_not-real")
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "report_not_found"

        traversal = client.get("/api/v1/reports/..%5Csecret.md")
        assert traversal.status_code == 404
        assert traversal.json()["error"]["code"] == "report_not_found"

        absolute = client.get("/api/v1/reports/C:%5CWindows%5Cwin.ini")
        assert absolute.status_code == 404
        assert absolute.json()["error"]["code"] == "report_not_found"

        unsupported = client.get("/api/v1/reports", params={"format": "html"})
        assert unsupported.status_code == 422
        assert unsupported.json()["error"]["code"] == "unsupported_report_format"


def test_reports_center_does_not_mutate_stage1_to_stage7_tables(db, tmp_path: Path) -> None:
    write_reports(tmp_path)
    before = protected_rows(db)
    with make_client(db, tmp_path) as client:
        listing = client.get("/api/v1/reports", params={"category": "risk_validation"}).json()
        reference = listing["reports"][0]["report_reference"]
        assert client.get("/api/v1/reports/categories").status_code == 200
        assert client.get("/api/v1/reports").status_code == 200
        assert client.get(f"/api/v1/reports/{reference}").status_code == 200
        assert client.get(f"/api/v1/reports/{reference}/download").status_code == 200
    assert protected_rows(db) == before
