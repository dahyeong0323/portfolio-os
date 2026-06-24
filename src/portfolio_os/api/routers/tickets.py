from datetime import timedelta

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database, get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.intents import IntentSummarySchema
from portfolio_os.api.schemas.risk import RiskValidationSchema
from portfolio_os.api.schemas.tickets import (
    CreateTicketRequest,
    CreateTicketResponse,
    OrderTicketDetailResponse,
    OrderTicketEventSchema,
    OrderTicketListResponse,
    OrderTicketSchema,
    TicketActionResponse,
    TicketDecisionRequest,
)
from portfolio_os.db import Database
from portfolio_os.intents import TransactionIntentRepository
from portfolio_os.journal.repository import DecisionJournalRepository
from portfolio_os.risk.repositories import RiskValidationRepository
from portfolio_os.serialization import loads_json
from portfolio_os.tickets import OrderTicketRepository, OrderTicketService
from portfolio_os.validators import utc_now

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=OrderTicketListResponse)
async def get_tickets(db: Database = Depends(get_database)) -> OrderTicketListResponse:
    tickets = OrderTicketRepository(db).list_all()
    return OrderTicketListResponse(
        count=len(tickets),
        tickets=[OrderTicketSchema.model_validate(ticket) for ticket in tickets],
    )


def _ticket_available_actions(status: str) -> list[str]:
    if status == "validated":
        return ["approve_ticket", "reject_ticket"]
    if status == "approved":
        return ["log_manual_execution"]
    return []


def _ticket_blocked_actions(status: str) -> list[str]:
    blocked = ["modify_deferred", "broker_write_not_available", "automatic_execution_not_available"]
    if status == "validated":
        blocked.append("manual_execution_requires_approval")
    elif status == "approved":
        blocked.extend(["approve_already_recorded", "reject_not_available_after_approval"])
    elif status == "executed_provisional":
        blocked.extend(["confirmation_available_via_executions_page", "approval_closed", "rejection_closed"])
    elif status == "reconciled":
        blocked.extend(["ticket_already_reconciled", "approval_closed", "rejection_closed"])
    else:
        blocked.extend(["ticket_not_actionable", "manual_execution_not_available"])
    return blocked


def _intent_summary(intent) -> IntentSummarySchema:
    return IntentSummarySchema(
        intent_id=intent.intent_id,
        status=intent.status,
        account_id=intent.account_id,
        instrument_id=intent.instrument_id,
        side=intent.intent_type,
        requested_quantity=intent.requested_quantity,
        requested_notional=intent.requested_notional,
        limit_price=intent.limit_price,
        currency=intent.currency,
        created_at=intent.created_at,
    )


def _event_schema(event) -> OrderTicketEventSchema:
    return OrderTicketEventSchema(
        event_id=event.event_id,
        order_ticket_id=event.order_ticket_id,
        event_type=event.event_type,
        from_status=event.from_status,
        to_status=event.to_status,
        event_payload=loads_json(event.event_payload_json or "{}"),
        created_at=event.created_at,
    )


def _ticket_detail_response(ticket, db: Database) -> OrderTicketDetailResponse:
    repo = OrderTicketRepository(db)
    validation = RiskValidationRepository(db).get(ticket.risk_validation_id)
    intent = TransactionIntentRepository(db).get(ticket.intent_id)
    return OrderTicketDetailResponse(
        ticket=OrderTicketSchema.model_validate(ticket),
        linked_risk_validation=RiskValidationSchema.model_validate(validation),
        linked_intent=_intent_summary(intent),
        ticket_events=[_event_schema(event) for event in repo.list_events(ticket.order_ticket_id)],
        available_actions=_ticket_available_actions(ticket.status),
        blocked_actions=_ticket_blocked_actions(ticket.status),
    )


def _ticket_action_response(ticket, db: Database, decision_type: str) -> TicketActionResponse:
    journal = DecisionJournalRepository(db).latest_for_ticket(ticket.order_ticket_id, decision_type)
    return TicketActionResponse(
        ticket_id=ticket.order_ticket_id,
        new_ticket_status=ticket.status,
        ticket=OrderTicketSchema.model_validate(ticket),
        ticket_events=[_event_schema(event) for event in OrderTicketRepository(db).list_events(ticket.order_ticket_id)],
        linked_decision_journal_entry_id=int(journal["decision_id"]) if journal is not None else None,
        available_actions=_ticket_available_actions(ticket.status),
        blocked_actions=_ticket_blocked_actions(ticket.status),
    )


@router.post("", response_model=CreateTicketResponse, status_code=201)
async def create_ticket(payload: CreateTicketRequest, db: Database = Depends(get_writable_database)) -> CreateTicketResponse:
    try:
        validation = RiskValidationRepository(db).get(payload.risk_validation_id)
    except ValueError as exc:
        raise ApiError(404, "risk_validation_not_found", "The risk validation result was not found.") from exc
    if validation.validation_status == "rejected":
        raise ApiError(409, "risk_validation_rejected", "Rejected risk validations cannot create order tickets.")
    expires_at = payload.expires_at or utc_now() + timedelta(days=1)
    try:
        ticket = OrderTicketService(db).create_ticket_from_validation(payload.risk_validation_id, expires_at)
    except ValueError as exc:
        raise ApiError(409, "ticket_create_blocked", "The order ticket could not be created from this validation.", str(exc)) from exc
    return CreateTicketResponse(
        ticket=OrderTicketSchema.model_validate(ticket),
        risk_validation_id=ticket.risk_validation_id,
        intent_id=ticket.intent_id,
        available_actions=_ticket_available_actions(ticket.status),
        blocked_actions=_ticket_blocked_actions(ticket.status),
    )


@router.post("/{ticket_id}/approve", response_model=TicketActionResponse)
async def approve_ticket(ticket_id: int, payload: TicketDecisionRequest, db: Database = Depends(get_writable_database)) -> TicketActionResponse:
    repo = OrderTicketRepository(db)
    try:
        ticket = repo.get(ticket_id)
    except ValueError as exc:
        raise ApiError(404, "ticket_not_found", "The order ticket was not found.") from exc
    if ticket.status != "validated":
        raise ApiError(409, "ticket_invalid_state", "Only validated tickets can be approved.", {"status": ticket.status})
    if ticket.expires_at < utc_now():
        raise ApiError(409, "ticket_expired", "Expired tickets cannot be approved.", {"expires_at": ticket.expires_at.isoformat()})
    try:
        approved = OrderTicketService(db).approve_ticket(ticket_id, payload.approval_note, payload.emotional_state)
    except ValueError as exc:
        raise ApiError(409, "ticket_approval_blocked", "The ticket could not be approved.", str(exc)) from exc
    return _ticket_action_response(approved, db, "ticket_approval")


@router.post("/{ticket_id}/reject", response_model=TicketActionResponse)
async def reject_ticket(ticket_id: int, payload: TicketDecisionRequest, db: Database = Depends(get_writable_database)) -> TicketActionResponse:
    if not payload.rejection_reason:
        raise ApiError(422, "rejection_reason_required", "A rejection reason is required.")
    repo = OrderTicketRepository(db)
    try:
        ticket = repo.get(ticket_id)
    except ValueError as exc:
        raise ApiError(404, "ticket_not_found", "The order ticket was not found.") from exc
    if ticket.status != "validated":
        raise ApiError(409, "ticket_invalid_state", "Only validated tickets can be rejected.", {"status": ticket.status})
    if ticket.expires_at < utc_now():
        raise ApiError(409, "ticket_expired", "Expired tickets cannot be rejected.", {"expires_at": ticket.expires_at.isoformat()})
    try:
        rejected = OrderTicketService(db).reject_ticket(ticket_id, payload.rejection_reason, payload.emotional_state)
    except ValueError as exc:
        raise ApiError(409, "ticket_rejection_blocked", "The ticket could not be rejected.", str(exc)) from exc
    return _ticket_action_response(rejected, db, "ticket_rejection")


@router.get("/{ticket_id}", response_model=OrderTicketDetailResponse)
async def get_ticket_detail(ticket_id: int, db: Database = Depends(get_database)) -> OrderTicketDetailResponse:
    try:
        ticket = OrderTicketRepository(db).get(ticket_id)
    except ValueError as exc:
        raise ApiError(404, "ticket_not_found", "The order ticket was not found.") from exc
    return _ticket_detail_response(ticket, db)
