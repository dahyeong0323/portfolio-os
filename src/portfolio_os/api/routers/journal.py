from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.journal import DecisionJournalEntrySchema, DecisionJournalListResponse
from portfolio_os.db import Database
from portfolio_os.journal import DecisionJournalRepository
from portfolio_os.serialization import loads_json
from portfolio_os.validators import datetime_from_text

router = APIRouter(prefix="/journal", tags=["journal"])


def _entry_schema(row: dict) -> DecisionJournalEntrySchema:
    return DecisionJournalEntrySchema(
        decision_id=row["decision_id"],
        decision_type=row["decision_type"],
        order_ticket_id=row["order_ticket_id"],
        override_ticket_id=row["override_ticket_id"],
        risk_validation_id=row["risk_validation_id"],
        manual_execution_id=row["manual_execution_id"],
        human_decision=row["human_decision"],
        reason=row["reason"],
        emotional_state=row["emotional_state"],
        context=loads_json(row["context_json"] or "{}"),
        created_at=datetime_from_text(row["created_at"]),
    )


@router.get("", response_model=DecisionJournalListResponse)
async def list_journal_entries(
    decision_type: str | None = None,
    linked_ticket_id: int | None = None,
    linked_override_id: int | None = None,
    linked_execution_id: int | None = None,
    risk_validation_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Database = Depends(get_database),
) -> DecisionJournalListResponse:
    safe_limit = max(1, min(limit, 200))
    safe_offset = max(0, offset)
    rows = DecisionJournalRepository(db).list_filtered(
        decision_type=decision_type,
        order_ticket_id=linked_ticket_id,
        override_ticket_id=linked_override_id,
        manual_execution_id=linked_execution_id,
        risk_validation_id=risk_validation_id,
        limit=safe_limit,
        offset=safe_offset,
    )
    return DecisionJournalListResponse(count=len(rows), entries=[_entry_schema(row) for row in rows])


@router.get("/{journal_id}", response_model=DecisionJournalEntrySchema)
async def get_journal_entry(journal_id: int, db: Database = Depends(get_database)) -> DecisionJournalEntrySchema:
    row = DecisionJournalRepository(db).get(journal_id)
    if row is None:
        raise ApiError(404, "journal_entry_not_found", "The decision journal entry was not found.")
    return _entry_schema(row)
