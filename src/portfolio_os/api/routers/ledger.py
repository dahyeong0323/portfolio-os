from datetime import date

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.schemas.ledger import LedgerSnapshotResponse, LedgerStatusResponse
from portfolio_os.api.serialization import parse_datetime
from portfolio_os.db import Database
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.repositories import ReconciliationRepository
from portfolio_os.state import LedgerStateMachine

router = APIRouter(prefix="/ledger", tags=["ledger"])

STATUS_EXPLANATIONS = {
    "reconciled": "The ledger matches the latest completed reconciliation and has no newer unconfirmed inputs.",
    "provisional": "The ledger has not been reconciled yet or contains newer unconfirmed inputs.",
    "stale": "The latest reconciled ledger is older than the allowed freshness window.",
    "broken": "The latest reconciliation found unresolved or out-of-tolerance differences.",
}


@router.get("/status", response_model=LedgerStatusResponse)
async def get_ledger_status(db: Database = Depends(get_database)) -> LedgerStatusResponse:
    status = LedgerStateMachine(db).get_current_status()
    latest_reconciled = ReconciliationRepository(db).get_latest_reconciled()
    last_reconciled_at = parse_datetime(latest_reconciled["completed_at"]) if latest_reconciled else None
    return LedgerStatusResponse(
        ledger_status=status,
        last_reconciled_at=last_reconciled_at,
        is_reconciled=status == "reconciled",
        is_provisional=status == "provisional",
        is_stale=status == "stale",
        is_broken=status == "broken",
        explanation=STATUS_EXPLANATIONS[status],
    )


@router.get("/snapshot", response_model=LedgerSnapshotResponse)
async def get_ledger_snapshot(
    as_of_date: date | None = None,
    db: Database = Depends(get_database),
) -> LedgerSnapshotResponse:
    snapshot = LedgerSnapshotBuilder(db).build_snapshot(as_of_date or date.today())
    return LedgerSnapshotResponse.model_validate(snapshot)
