from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends

from portfolio_os.api.deps import get_database, get_writable_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.schemas.executions import (
    ConfirmExecutionsRequest,
    ConfirmExecutionsResponse,
    LinkedTicketSummary,
    LogManualExecutionRequest,
    ManualExecutionResponse,
    ManualExecutionSchema,
    PendingExecutionListResponse,
    PendingExecutionSchema,
    ProvisionalTransactionSchema,
    ReconciliationEvidenceSchema,
    SkippedExecutionSchema,
)
from portfolio_os.api.schemas.tickets import OrderTicketSchema
from portfolio_os.db import Database
from portfolio_os.execution import ManualExecutionRepository, ManualExecutionService
from portfolio_os.repositories import ReconciliationRepository, TransactionRepository
from portfolio_os.tickets import OrderTicketRepository
from portfolio_os.validators import date_from_text, datetime_from_text

router = APIRouter(prefix="/executions", tags=["executions"])


def _ensure_non_negative(value: Decimal, field_name: str) -> None:
    if value < 0:
        raise ApiError(422, "negative_amount", f"{field_name} cannot be negative.", {"field": field_name})


def _linked_ticket_summary(db: Database, order_ticket_id: int | None) -> LinkedTicketSummary | None:
    if order_ticket_id is None:
        return None
    try:
        ticket = OrderTicketRepository(db).get(order_ticket_id)
    except ValueError:
        return None
    return LinkedTicketSummary(
        order_ticket_id=ticket.order_ticket_id,
        status=ticket.status,
        side=ticket.side,
        instrument_id=ticket.instrument_id,
        ticket_quantity=ticket.ticket_quantity,
        ticket_notional=ticket.ticket_notional,
        currency=ticket.currency,
    )


def _reconciliation_evidence_schema(row: dict | None) -> ReconciliationEvidenceSchema | None:
    if row is None:
        return None
    return ReconciliationEvidenceSchema(
        reconciliation_id=row["reconciliation_id"],
        account_id=row["account_id"],
        as_of_date=date_from_text(row["as_of_date"]),
        reconciliation_status=row["reconciliation_status"],
        completed_at=datetime_from_text(row["completed_at"]) if row["completed_at"] else None,
    )


def _latest_evidence_for_execution(db: Database, execution) -> dict | None:
    repo = ReconciliationRepository(db)
    if execution.reconciliation_id is not None:
        return repo.get_reconciliation(execution.reconciliation_id)
    return repo.get_latest_reconciliation(execution.account_id)


def _confirmation_readiness(execution, db: Database) -> tuple[bool, str | None, bool | None, dict | None]:
    evidence = _latest_evidence_for_execution(db, execution)
    tx = TransactionRepository(db).get_transaction(execution.created_transaction_id) if execution.created_transaction_id is not None else None
    transaction_is_confirmed = tx.is_confirmed if tx is not None else None
    if execution.execution_status != "pending_reconciliation":
        return False, "execution_not_pending", transaction_is_confirmed, evidence
    if execution.override_ticket_id is not None:
        return False, "override_execution_deferred", transaction_is_confirmed, evidence
    if execution.created_transaction_id is None:
        return False, "missing_provisional_transaction", transaction_is_confirmed, evidence
    if tx is None:
        return False, "provisional_transaction_not_found", transaction_is_confirmed, evidence
    if not tx.is_confirmed:
        return False, "transaction_not_confirmed", transaction_is_confirmed, evidence
    if evidence is None:
        return False, "reconciliation_not_available", transaction_is_confirmed, evidence
    if evidence["reconciliation_status"] != "passed":
        return False, "reconciliation_not_passed", transaction_is_confirmed, evidence
    if evidence["account_id"] is not None and evidence["account_id"] != execution.account_id:
        return False, "reconciliation_account_mismatch", transaction_is_confirmed, evidence
    evidence_date = date_from_text(evidence["as_of_date"])
    if execution.executed_at.date() > evidence_date or tx.trade_date > evidence_date:
        return False, "execution_after_reconciliation", transaction_is_confirmed, evidence
    return True, None, transaction_is_confirmed, evidence


def _execution_available_actions(status: str, confirmation_eligible: bool) -> list[str]:
    if status == "pending_reconciliation" and confirmation_eligible:
        return ["confirm_after_reconciliation"]
    if status == "pending_reconciliation":
        return ["await_reconciliation"]
    return []


def _execution_blocked_actions(status: str, confirmation_eligible: bool, blocked_reason: str | None) -> list[str]:
    blocked = ["broker_write_not_available", "automatic_execution_not_available"]
    if status == "pending_reconciliation" and not confirmation_eligible:
        blocked.append(blocked_reason or "manual_confirmation_requires_reconciliation")
    elif status == "pending_reconciliation":
        blocked.append("broker_execution_not_available")
    else:
        blocked.append("execution_not_pending")
    return blocked


def _pending_execution_schema(execution, db: Database) -> PendingExecutionSchema:
    eligible, reason, transaction_is_confirmed, evidence = _confirmation_readiness(execution, db)
    return PendingExecutionSchema(
        **ManualExecutionSchema.model_validate(execution).model_dump(),
        linked_ticket=_linked_ticket_summary(db, execution.order_ticket_id),
        pending_reconciliation=execution.execution_status == "pending_reconciliation",
        transaction_is_confirmed=transaction_is_confirmed,
        reconciliation_evidence=_reconciliation_evidence_schema(evidence),
        confirmation_eligible=eligible,
        confirmation_blocked_reason=reason,
        available_actions=_execution_available_actions(execution.execution_status, eligible),
        blocked_actions=_execution_blocked_actions(execution.execution_status, eligible, reason),
    )


def _provisional_transaction_schema(db: Database, transaction_id: int | None) -> ProvisionalTransactionSchema | None:
    if transaction_id is None:
        return None
    tx = TransactionRepository(db).get_transaction(transaction_id)
    if tx is None:
        return None
    return ProvisionalTransactionSchema(
        transaction_id=tx.transaction_id,
        account_id=tx.account_id,
        instrument_id=tx.instrument_id,
        transaction_type=tx.transaction_type,
        trade_date=tx.trade_date,
        currency=tx.currency,
        quantity=tx.quantity,
        price=tx.price,
        gross_amount=tx.gross_amount,
        fee_amount=tx.fee_amount,
        tax_amount=tx.tax_amount,
        net_cash_amount=tx.net_cash_amount,
        source=tx.source,
        external_ref=tx.external_ref,
        is_confirmed=tx.is_confirmed,
    )


def _manual_execution_response(execution, db: Database) -> ManualExecutionResponse:
    eligible, reason, transaction_is_confirmed, evidence = _confirmation_readiness(execution, db)
    linked_ticket = None
    if execution.order_ticket_id is not None:
        try:
            linked_ticket = OrderTicketSchema.model_validate(OrderTicketRepository(db).get(execution.order_ticket_id))
        except ValueError:
            linked_ticket = None
    return ManualExecutionResponse(
        execution_id=execution.manual_execution_id,
        execution_status=execution.execution_status,
        created_transaction_id=execution.created_transaction_id,
        linked_ticket_id=execution.order_ticket_id,
        execution=ManualExecutionSchema.model_validate(execution),
        linked_ticket=linked_ticket,
        provisional_transaction=_provisional_transaction_schema(db, execution.created_transaction_id),
        pending_reconciliation=execution.execution_status == "pending_reconciliation",
        transaction_is_confirmed=transaction_is_confirmed,
        reconciliation_evidence=_reconciliation_evidence_schema(evidence),
        confirmation_eligible=eligible,
        confirmation_blocked_reason=reason,
        available_actions=_execution_available_actions(execution.execution_status, eligible),
        blocked_actions=_execution_blocked_actions(execution.execution_status, eligible, reason),
        explanation="Manual execution was recorded as a provisional transaction and awaits reconciliation. Portfolio OS did not place a broker order.",
    )


@router.get("/pending", response_model=PendingExecutionListResponse)
async def get_pending_executions(db: Database = Depends(get_database)) -> PendingExecutionListResponse:
    executions = ManualExecutionRepository(db).list_pending()
    return PendingExecutionListResponse(
        count=len(executions),
        executions=[_pending_execution_schema(execution, db) for execution in executions],
    )


@router.post("/confirm-after-reconciliation", response_model=ConfirmExecutionsResponse)
async def confirm_after_reconciliation(payload: ConfirmExecutionsRequest, db: Database = Depends(get_writable_database)) -> ConfirmExecutionsResponse:
    try:
        result = ManualExecutionService(db).confirm_after_reconciliation(
            confirmation_run_id=f"stage6-{uuid4()}",
            reconciliation_id=payload.reconciliation_id,
            account_id=payload.account_id,
            as_of_date=payload.as_of_date,
            execution_ids=payload.execution_ids,
        )
    except ValueError as exc:
        raise ApiError(409, "confirmation_blocked", "Manual execution confirmation requires matching passed reconciliation evidence.", str(exc)) from exc
    return ConfirmExecutionsResponse(
        confirmation_run_id=result.confirmation_run_id,
        reconciliation_id_used=result.reconciliation_id_used,
        total_pending_checked=result.total_pending_checked,
        confirmed_execution_ids=result.confirmed_execution_ids,
        still_pending_execution_ids=result.still_pending_execution_ids,
        failed_execution_ids=result.failed_execution_ids,
        skipped_executions=[SkippedExecutionSchema.model_validate(item) for item in result.skipped_executions],
        explanation=result.explanation,
    )


@router.post("", response_model=ManualExecutionResponse, status_code=201)
async def log_manual_execution(payload: LogManualExecutionRequest, db: Database = Depends(get_writable_database)) -> ManualExecutionResponse:
    _ensure_non_negative(payload.filled_quantity, "filled_quantity")
    _ensure_non_negative(payload.fill_price, "fill_price")
    _ensure_non_negative(payload.fee, "fee")
    _ensure_non_negative(payload.tax, "tax")
    if payload.filled_quantity == 0:
        raise ApiError(422, "zero_quantity", "filled_quantity must be greater than zero.")
    try:
        ticket = OrderTicketRepository(db).get(payload.ticket_id)
    except ValueError as exc:
        raise ApiError(404, "ticket_not_found", "The order ticket was not found.") from exc
    if ticket.status != "approved":
        raise ApiError(409, "manual_execution_blocked", "Manual execution logging requires an approved ticket.", {"status": ticket.status})
    try:
        execution = ManualExecutionService(db).log_execution_for_ticket(
            payload.ticket_id,
            payload.filled_quantity,
            payload.fill_price,
            payload.fee,
            payload.tax,
            payload.executed_at,
            payload.broker_reference,
            payload.notes,
        )
    except ValueError as exc:
        raise ApiError(409, "manual_execution_blocked", "The manual execution could not be logged.", str(exc)) from exc
    return _manual_execution_response(execution, db)


@router.get("/{execution_id}", response_model=ManualExecutionResponse)
async def get_execution_detail(execution_id: int, db: Database = Depends(get_database)) -> ManualExecutionResponse:
    try:
        execution = ManualExecutionRepository(db).get(execution_id)
    except ValueError as exc:
        raise ApiError(404, "execution_not_found", "The manual execution was not found.") from exc
    return _manual_execution_response(execution, db)
