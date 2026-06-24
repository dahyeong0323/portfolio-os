from decimal import Decimal

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database, get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.routers.journal import _entry_schema
from portfolio_os.api.routers.postmortems import postmortem_schema
from portfolio_os.api.schemas.overrides import (
    DeclareOverrideRequest,
    OverrideActionRequest,
    OverrideListResponse,
    OverrideResponse,
    OverrideTicketSchema,
)
from portfolio_os.db import Database
from portfolio_os.journal import DecisionJournalRepository, PostmortemTaskRepository
from portfolio_os.override import OverrideService, OverrideTicketRepository
from portfolio_os.repositories import AccountRepository, InstrumentRepository

router = APIRouter(prefix="/overrides", tags=["overrides"])

OPEN_OVERRIDE_STATUSES = {"declared", "risk_warned", "human_confirmed"}


def _ensure_non_negative(value: Decimal | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ApiError(422, "negative_amount", f"{field_name} cannot be negative.", {"field": field_name})


def _override_actions(status: str) -> tuple[list[str], list[str]]:
    blocked = ["override_execution_deferred", "broker_write_not_available", "automatic_execution_not_available"]
    if status in {"declared", "risk_warned"}:
        return ["confirm_override", "cancel_override"], blocked
    if status == "human_confirmed":
        return ["cancel_override"], blocked + ["override_already_confirmed"]
    return [], blocked + ["override_not_actionable"]


def _linked_postmortem_id(db: Database, override_id: int) -> int | None:
    row = PostmortemTaskRepository(db).latest_for_override(override_id)
    return int(row["postmortem_task_id"]) if row else None


def _override_schema(override, db: Database) -> OverrideTicketSchema:
    available, blocked = _override_actions(override.status)
    account = AccountRepository(db).get_account(override.account_id)
    instrument = InstrumentRepository(db).get_instrument(override.instrument_id) if override.instrument_id is not None else None
    return OverrideTicketSchema(
        override_id=override.override_ticket_id,
        status=override.status,
        override_type=override.override_type,
        account_id=override.account_id,
        account_name=account.account_name if account else None,
        instrument_id=override.instrument_id,
        instrument_symbol=instrument.symbol if instrument else None,
        instrument_name=instrument.instrument_name if instrument else None,
        side=override.side,
        requested_quantity=override.requested_quantity,
        requested_notional=override.requested_notional,
        currency=override.currency,
        human_reason=override.human_reason,
        human_final_choice=override.human_final_choice,
        risk_warning=override.risk_warning,
        ledger_status_at_declaration=override.ledger_status_at_declaration,
        mandatory_reconciliation_deadline=override.mandatory_reconciliation_deadline,
        mandatory_postmortem_date=override.mandatory_postmortem_date,
        created_at=override.created_at,
        updated_at=override.updated_at,
        linked_postmortem_task_id=_linked_postmortem_id(db, override.override_ticket_id),
        available_actions=available,
        blocked_actions=blocked,
    )


def _override_response(override, db: Database, explanation: str) -> OverrideResponse:
    journal_rows = DecisionJournalRepository(db).list_filtered(override_ticket_id=override.override_ticket_id)
    postmortem_row = PostmortemTaskRepository(db).latest_for_override(override.override_ticket_id)
    return OverrideResponse(
        override=_override_schema(override, db),
        linked_journal_entries=[_entry_schema(row) for row in journal_rows],
        postmortem_task=postmortem_schema(postmortem_row) if postmortem_row else None,
        explanation=explanation,
    )


def _schedule_postmortem_if_missing(db: Database, override) -> None:
    if override.mandatory_postmortem_date is None:
        return
    repo = PostmortemTaskRepository(db)
    if repo.latest_for_override(override.override_ticket_id) is not None:
        return
    repo.schedule(override.mandatory_postmortem_date, override_ticket_id=override.override_ticket_id)


@router.get("", response_model=OverrideListResponse)
async def list_overrides(db: Database = Depends(get_database)) -> OverrideListResponse:
    overrides = OverrideTicketRepository(db).list_all()
    return OverrideListResponse(
        count=len(overrides),
        open_count=sum(1 for override in overrides if override.status in OPEN_OVERRIDE_STATUSES),
        overrides=[_override_schema(override, db) for override in overrides],
    )


@router.post("", response_model=OverrideResponse, status_code=201)
async def declare_override(payload: DeclareOverrideRequest, db: Database = Depends(get_writable_database)) -> OverrideResponse:
    if not payload.human_reason.strip():
        raise ApiError(422, "human_reason_required", "Override declaration requires an explicit human reason.")
    _ensure_non_negative(payload.requested_quantity, "requested_quantity")
    _ensure_non_negative(payload.requested_notional, "requested_notional")
    try:
        AccountRepository(db).get_account(payload.account_id)
    except ValueError as exc:
        raise ApiError(404, "account_not_found", "The account was not found.") from exc
    if payload.instrument_id is not None:
        try:
            InstrumentRepository(db).get_instrument(payload.instrument_id)
        except ValueError as exc:
            raise ApiError(404, "instrument_not_found", "The instrument was not found.") from exc
    try:
        override = OverrideService(db).declare_override(
            payload.override_type,
            payload.account_id,
            payload.instrument_id,
            payload.side,
            payload.requested_quantity,
            payload.requested_notional,
            payload.currency,
            payload.human_reason.strip(),
            payload.emotional_state,
        )
        _schedule_postmortem_if_missing(db, override)
    except ValueError as exc:
        raise ApiError(409, "override_declare_blocked", "The override could not be declared.", str(exc)) from exc
    return _override_response(override, db, "Override was declared as an explicit exception. No broker order was placed and no official risk-validated ticket was created.")


@router.get("/{override_id}", response_model=OverrideResponse)
async def get_override_detail(override_id: int, db: Database = Depends(get_database)) -> OverrideResponse:
    try:
        override = OverrideTicketRepository(db).get(override_id)
    except ValueError as exc:
        raise ApiError(404, "override_not_found", "The override was not found.") from exc
    return _override_response(override, db, "Override detail is an audit record, not a recommendation.")


@router.post("/{override_id}/confirm", response_model=OverrideResponse)
async def confirm_override(override_id: int, payload: OverrideActionRequest, db: Database = Depends(get_writable_database)) -> OverrideResponse:
    try:
        current = OverrideTicketRepository(db).get(override_id)
    except ValueError as exc:
        raise ApiError(404, "override_not_found", "The override was not found.") from exc
    if current.status not in {"declared", "risk_warned"}:
        raise ApiError(409, "override_confirm_blocked", "Only declared or risk-warned overrides can be confirmed.", {"status": current.status})
    override = OverrideService(db).confirm_override(override_id, "execute", payload.emotional_state)
    return _override_response(override, db, "Override was human-confirmed. This is still not broker execution and no order was placed.")


@router.post("/{override_id}/cancel", response_model=OverrideResponse)
async def cancel_override(override_id: int, payload: OverrideActionRequest, db: Database = Depends(get_writable_database)) -> OverrideResponse:
    try:
        current = OverrideTicketRepository(db).get(override_id)
    except ValueError as exc:
        raise ApiError(404, "override_not_found", "The override was not found.") from exc
    if current.status in {"cancelled", "executed_provisional", "reconciled", "postmortem_completed"}:
        raise ApiError(409, "override_cancel_blocked", "This override can no longer be cancelled.", {"status": current.status})
    override = OverrideService(db).confirm_override(override_id, "cancel", payload.emotional_state)
    return _override_response(override, db, "Override was cancelled. No broker order was placed.")
