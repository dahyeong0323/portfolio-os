from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request, status

from portfolio_os.api.artifacts import report_path, resolve_snapshot_artifact
from portfolio_os.api.deps import get_database, get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.reconciliation import (
    LatestReconciliationResponse,
    ReconciliationReportResponse,
    ReconciliationSnapshotSchema,
    RunReconciliationRequest,
    RunReconciliationResponse,
)
from portfolio_os.api.serialization import parse_date, parse_datetime, parse_decimal, parse_json_list
from portfolio_os.db import Database
from portfolio_os.importers import load_external_snapshot
from portfolio_os.reconciliation import ReconciliationWorkflowService
from portfolio_os.repositories import AccountRepository
from portfolio_os.repositories import ReconciliationRepository

router = APIRouter(prefix="/reconciliations", tags=["reconciliation"])


def _reconciliation_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "reconciliation_id": row["reconciliation_id"],
        "account_id": row["account_id"],
        "as_of_date": parse_date(row["as_of_date"]),
        "started_at": parse_datetime(row["started_at"]),
        "completed_at": parse_datetime(row["completed_at"]),
        "ledger_status_before": row["ledger_status_before"],
        "ledger_status_after": row["ledger_status_after"],
        "reconciliation_status": row["reconciliation_status"],
        "snapshot_source": row["snapshot_source"],
        "position_diff_count": row["position_diff_count"],
        "cash_diff_count": row["cash_diff_count"],
        "liability_diff_count": row["liability_diff_count"],
        "tax_reserve_diff_count": row["tax_reserve_diff_count"],
        "total_abs_cash_diff_base": parse_decimal(row["total_abs_cash_diff_base"], "total_abs_cash_diff_base"),
        "tolerance": {
            "cash_abs": parse_decimal(row["tolerance_cash_abs"], "tolerance_cash_abs"),
            "quantity_abs": parse_decimal(row["tolerance_quantity_abs"], "tolerance_quantity_abs"),
        },
        "expected_positions": parse_json_list(row["expected_positions_json"], "expected_positions_json"),
        "actual_positions": parse_json_list(row["actual_positions_json"], "actual_positions_json"),
        "position_differences": parse_json_list(row["position_diffs_json"], "position_diffs_json"),
        "expected_cash": parse_json_list(row["expected_cash_json"], "expected_cash_json"),
        "actual_cash": parse_json_list(row["actual_cash_json"], "actual_cash_json"),
        "cash_differences": parse_json_list(row["cash_diffs_json"], "cash_diffs_json"),
        "expected_liabilities": parse_json_list(row["expected_liabilities_json"], "expected_liabilities_json"),
        "actual_liabilities": parse_json_list(row["actual_liabilities_json"], "actual_liabilities_json"),
        "liability_differences": parse_json_list(row["liability_diffs_json"], "liability_diffs_json"),
        "expected_tax_reserves": parse_json_list(row["expected_tax_reserves_json"], "expected_tax_reserves_json"),
        "actual_tax_reserves": parse_json_list(row["actual_tax_reserves_json"], "actual_tax_reserves_json"),
        "tax_reserve_differences": parse_json_list(row["tax_reserve_diffs_json"], "tax_reserve_diffs_json"),
        "failure_reason": row["failure_reason"],
        "created_at": parse_datetime(row["created_at"]),
    }


@router.get("/latest", response_model=LatestReconciliationResponse)
async def get_latest_reconciliation(db: Database = Depends(get_database)) -> LatestReconciliationResponse:
    latest = ReconciliationRepository(db).get_latest_reconciliation()
    if latest is None:
        return LatestReconciliationResponse(found=False, reconciliation=None)
    return LatestReconciliationResponse(
        found=True,
        reconciliation=ReconciliationSnapshotSchema.model_validate(_reconciliation_payload(latest)),
    )


@router.post("", response_model=RunReconciliationResponse, status_code=status.HTTP_201_CREATED)
async def run_reconciliation(
    payload: RunReconciliationRequest,
    request: Request,
    db: Database = Depends(get_writable_database),
) -> RunReconciliationResponse:
    if AccountRepository(db).get_account(payload.account_id) is None:
        raise ApiError(404, "account_not_found", "The selected account was not found.")

    metadata, snapshot_path = resolve_snapshot_artifact(
        Path(request.app.state.snapshot_dir),
        payload.artifact_id,
    )
    if metadata.account_id != payload.account_id:
        raise ApiError(422, "snapshot_account_mismatch", "The snapshot artifact belongs to a different account.")
    if payload.as_of_date is not None and payload.as_of_date != metadata.as_of_date:
        raise ApiError(422, "snapshot_date_mismatch", "The requested date does not match the snapshot artifact date.")
    try:
        snapshot = load_external_snapshot(snapshot_path)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ApiError(422, "invalid_snapshot_artifact", "The external snapshot artifact is invalid.") from exc

    outcome = ReconciliationWorkflowService(db).run(
        snapshot,
        payload.account_id,
        Path(request.app.state.report_dir),
    )
    saved = outcome.reconciliation
    if saved.reconciliation_id is None:
        raise ApiError(500, "reconciliation_not_saved", "The reconciliation result was not saved.")
    explanation = {
        "passed": "The external snapshot matches ledger truth within tolerance.",
        "failed": "One or more differences exceed the allowed tolerance.",
        "needs_review": "One or more instruments could not be matched unambiguously.",
    }[saved.reconciliation_status]
    report_available = outcome.markdown_report is not None and outcome.markdown_report.is_file()
    return RunReconciliationResponse(
        reconciliation_id=saved.reconciliation_id,
        reconciliation_status=saved.reconciliation_status,
        ledger_status=saved.ledger_status_after,
        generated_at=saved.completed_at,
        diff_counts={
            "positions": sum(not item.within_tolerance for item in saved.position_differences),
            "cash": sum(not item.within_tolerance for item in saved.cash_differences),
            "liabilities": sum(not item.within_tolerance for item in saved.liability_differences),
            "tax_reserves": sum(not item.within_tolerance for item in saved.tax_reserve_differences),
        },
        report_available=report_available,
        report_reference=f"reconciliation:{saved.reconciliation_id}:markdown" if report_available else None,
        explanation=explanation,
        warnings=list(outcome.warnings),
    )


@router.get("/{reconciliation_id}", response_model=ReconciliationSnapshotSchema)
async def get_reconciliation(
    reconciliation_id: int,
    db: Database = Depends(get_database),
) -> ReconciliationSnapshotSchema:
    row = ReconciliationRepository(db).get_reconciliation(reconciliation_id)
    if row is None:
        raise ApiError(404, "reconciliation_not_found", "The reconciliation result was not found.")
    return ReconciliationSnapshotSchema.model_validate(_reconciliation_payload(row))


@router.get("/{reconciliation_id}/report", response_model=ReconciliationReportResponse)
async def get_reconciliation_report(
    reconciliation_id: int,
    request: Request,
    db: Database = Depends(get_database),
) -> ReconciliationReportResponse:
    if ReconciliationRepository(db).get_reconciliation(reconciliation_id) is None:
        raise ApiError(404, "reconciliation_not_found", "The reconciliation result was not found.")
    path = report_path(Path(request.app.state.report_dir), reconciliation_id)
    try:
        content = path.read_text(encoding="utf-8")
        generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError as exc:
        raise ApiError(404, "reconciliation_report_not_found", "The reconciliation report was not found.") from exc
    return ReconciliationReportResponse(
        reconciliation_id=reconciliation_id,
        format="markdown",
        content=content,
        generated_at=generated_at,
        report_reference=f"reconciliation:{reconciliation_id}:markdown",
    )
