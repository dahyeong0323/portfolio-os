from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from portfolio_os.api.app import create_app
from portfolio_os.models import Transaction
from portfolio_os.repositories import TransactionRepository
from tests.conftest import seed_account, seed_buy, seed_cash_anchor, seed_instrument


def make_client(db, tmp_path: Path, upload_limit_bytes: int = 5 * 1024 * 1024) -> TestClient:
    return TestClient(
        create_app(
            db.db_path,
            app_mode="test-reconciliation",
            snapshot_dir=tmp_path / "imports",
            report_dir=tmp_path / "reports",
            upload_limit_bytes=upload_limit_bytes,
        )
    )


def import_snapshot(
    client: TestClient,
    account_id: int,
    *,
    positions: str | None = "symbol,currency,quantity,exchange\nAAPL,USD,1,NASDAQ\n",
    cash: str | None = "currency,amount\nUSD,9900\n",
) -> dict:
    files = {}
    if positions is not None:
        files["positions_file"] = ("positions.csv", positions.encode(), "text/csv")
    if cash is not None:
        files["cash_file"] = ("cash.csv", cash.encode(), "text/csv")
    response = client.post(
        "/api/v1/snapshots/external-imports",
        data={"account_id": str(account_id), "as_of_date": "2026-01-03"},
        files=files,
    )
    assert response.status_code == 201, response.text
    return response.json()


def protected_stage2_rows(db) -> dict[str, list[dict]]:
    return {
        table: db.fetch_all(f"SELECT * FROM {table} ORDER BY 1")
        for table in ("risk_validation_results", "order_tickets", "manual_execution_logs", "override_tickets")
    }


def test_import_run_fetch_report_and_preserve_external_cash_boundary(db, tmp_path: Path) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)
    cash_before = db.fetch_all("SELECT * FROM cash_balances ORDER BY cash_balance_id")
    protected_before = protected_stage2_rows(db)

    with make_client(db, tmp_path) as client:
        imported = import_snapshot(client, account_id)
        assert imported["status"] == "imported"
        assert imported["counts"] == {"positions": 1, "cash": 1, "liabilities": 0, "tax_reserves": 0}
        assert imported["warnings"] == []

        after_import = db.fetch_all("SELECT * FROM cash_balances ORDER BY cash_balance_id")
        assert after_import == cash_before

        run = client.post(
            "/api/v1/reconciliations",
            json={
                "artifact_id": imported["artifact_id"],
                "account_id": account_id,
                "as_of_date": "2026-01-03",
            },
        )
        assert run.status_code == 201, run.text
        result = run.json()
        assert result["reconciliation_status"] == "passed"
        assert result["ledger_status"] == "reconciled"
        assert result["report_available"] is True
        reconciliation_id = result["reconciliation_id"]

        detail = client.get(f"/api/v1/reconciliations/{reconciliation_id}")
        assert detail.status_code == 200
        assert detail.json()["actual_cash"][0]["amount"] == "9900"
        assert client.get("/api/v1/reconciliations/latest").json()["reconciliation"]["reconciliation_id"] == reconciliation_id

        report = client.get(f"/api/v1/reconciliations/{reconciliation_id}/report")
        assert report.status_code == 200
        assert report.json()["format"] == "markdown"
        assert f"Reconciliation ID: {reconciliation_id}" in report.json()["content"]

    cash_after = db.fetch_all("SELECT * FROM cash_balances ORDER BY cash_balance_id")
    assert [(row["amount"], row["cash_balance_id"]) for row in cash_after] == [
        (row["amount"], row["cash_balance_id"]) for row in cash_before
    ]
    assert cash_after[0]["is_reconciled"] == 1
    assert protected_stage2_rows(db) == protected_before


def test_import_reports_unmatched_instrument_and_needs_review_does_not_confirm(db, tmp_path: Path) -> None:
    account_id = seed_account(db)
    seed_cash_anchor(db, account_id)

    with make_client(db, tmp_path) as client:
        imported = import_snapshot(
            client,
            account_id,
            positions="symbol,currency,quantity\nUNKNOWN,USD,1\n",
            cash="currency,amount\nUSD,10000\n",
        )
        assert imported["status"] == "imported_with_warnings"
        assert "UNKNOWN" in imported["warnings"][0]

        response = client.post(
            "/api/v1/reconciliations",
            json={"artifact_id": imported["artifact_id"], "account_id": account_id},
        )
        assert response.status_code == 201
        assert response.json()["reconciliation_status"] == "needs_review"
        assert response.json()["ledger_status"] == "broken"

    assert db.fetch_one("SELECT is_reconciled FROM cash_balances")["is_reconciled"] == 0


def test_failed_reconciliation_does_not_confirm_internal_inputs(db, tmp_path: Path) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    transaction_id = seed_buy(db, account_id, instrument_id)

    with make_client(db, tmp_path) as client:
        imported = import_snapshot(client, account_id, cash="currency,amount\nUSD,9800\n")
        response = client.post(
            "/api/v1/reconciliations",
            json={"artifact_id": imported["artifact_id"], "account_id": account_id},
        )
        assert response.status_code == 201
        assert response.json()["reconciliation_status"] == "failed"

    assert db.fetch_one("SELECT is_confirmed FROM transactions WHERE transaction_id = ?", (transaction_id,))["is_confirmed"] == 0
    assert db.fetch_one("SELECT is_reconciled FROM cash_balances")["is_reconciled"] == 0


def test_passed_reconciliation_does_not_confirm_future_transactions(db, tmp_path: Path) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    future = Transaction(
        0,
        account_id,
        instrument_id,
        "buy",
        date(2026, 2, 1),
        None,
        "USD",
        Decimal("1"),
        Decimal("100"),
        Decimal("100"),
        Decimal("0"),
        Decimal("0"),
        Decimal("-100"),
        None,
        "manual",
        None,
        None,
        False,
        False,
        None,
    )
    future_id = TransactionRepository(db).record_transaction(future).transaction_id

    with make_client(db, tmp_path) as client:
        imported = import_snapshot(client, account_id, positions=None, cash="currency,amount\nUSD,10000\n")
        response = client.post(
            "/api/v1/reconciliations",
            json={"artifact_id": imported["artifact_id"], "account_id": account_id},
        )
        assert response.status_code == 201
        assert response.json()["reconciliation_status"] == "passed"

    assert db.fetch_one("SELECT is_confirmed FROM transactions WHERE transaction_id = ?", (future_id,))["is_confirmed"] == 0


def test_invalid_uploads_and_artifact_references_return_structured_errors(db, tmp_path: Path) -> None:
    account_id = seed_account(db)
    with make_client(db, tmp_path) as client:
        missing = client.post(
            "/api/v1/snapshots/external-imports",
            data={"account_id": str(account_id), "as_of_date": "2026-01-03"},
        )
        assert missing.status_code == 422
        assert missing.json()["error"]["code"] == "snapshot_files_required"

        headers = client.post(
            "/api/v1/snapshots/external-imports",
            data={"account_id": str(account_id), "as_of_date": "2026-01-03"},
            files={"cash_file": ("cash.csv", b"wrong,value\nUSD,100\n", "text/csv")},
        )
        assert headers.status_code == 422
        assert headers.json()["error"]["code"] == "invalid_snapshot_headers"

        traversal = client.post(
            "/api/v1/reconciliations",
            json={"artifact_id": "../outside", "account_id": account_id},
        )
        assert traversal.status_code == 404
        assert traversal.json()["error"]["code"] == "snapshot_artifact_not_found"

        assert client.get("/api/v1/reconciliations/999999").status_code == 404
        assert client.get("/api/v1/reconciliations/999999/report").status_code == 404

    with make_client(db, tmp_path / "small", upload_limit_bytes=8) as client:
        too_large = client.post(
            "/api/v1/snapshots/external-imports",
            data={"account_id": str(account_id), "as_of_date": "2026-01-03"},
            files={"cash_file": ("cash.csv", b"currency,amount\nUSD,10000\n", "text/csv")},
        )
        assert too_large.status_code == 413
        assert too_large.json()["error"]["code"] == "snapshot_file_too_large"


def test_openapi_exposes_only_the_intended_stage3_mutations(db, tmp_path: Path) -> None:
    with make_client(db, tmp_path) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert set(paths["/api/v1/snapshots/external-imports"]) == {"post"}
    assert set(paths["/api/v1/reconciliations"]) == {"post"}
    assert set(paths["/api/v1/reconciliations/{reconciliation_id}"]) == {"get"}
    assert set(paths["/api/v1/reconciliations/{reconciliation_id}/report"]) == {"get"}
