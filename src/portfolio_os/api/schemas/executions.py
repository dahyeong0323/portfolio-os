from datetime import date, datetime
from decimal import Decimal

from portfolio_os.api.schemas import ApiSchema
from portfolio_os.api.schemas.tickets import OrderTicketSchema


class ManualExecutionSchema(ApiSchema):
    manual_execution_id: int
    order_ticket_id: int | None
    override_ticket_id: int | None
    created_transaction_id: int | None
    account_id: int
    instrument_id: int
    side: str
    executed_quantity: Decimal
    executed_price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    currency: str
    executed_at: datetime
    broker_execution_ref: str | None
    execution_status: str
    reconciliation_deadline: date | None
    reconciled_at: datetime | None
    reconciliation_id: int | None
    notes: str | None


class LinkedTicketSummary(ApiSchema):
    order_ticket_id: int
    status: str
    side: str
    instrument_id: int
    ticket_quantity: Decimal
    ticket_notional: Decimal
    currency: str


class ReconciliationEvidenceSchema(ApiSchema):
    reconciliation_id: int
    account_id: int | None
    as_of_date: date
    reconciliation_status: str
    completed_at: datetime | None


class PendingExecutionSchema(ManualExecutionSchema):
    linked_ticket: LinkedTicketSummary | None = None
    pending_reconciliation: bool
    transaction_is_confirmed: bool | None
    reconciliation_evidence: ReconciliationEvidenceSchema | None
    confirmation_eligible: bool
    confirmation_blocked_reason: str | None
    available_actions: list[str]
    blocked_actions: list[str]


class PendingExecutionListResponse(ApiSchema):
    count: int
    executions: list[PendingExecutionSchema]


class LogManualExecutionRequest(ApiSchema):
    ticket_id: int
    filled_quantity: Decimal
    fill_price: Decimal
    fee: Decimal
    tax: Decimal
    executed_at: datetime
    broker_reference: str | None = None
    notes: str | None = None


class ProvisionalTransactionSchema(ApiSchema):
    transaction_id: int
    account_id: int
    instrument_id: int
    transaction_type: str
    trade_date: date
    currency: str
    quantity: Decimal
    price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    source: str
    external_ref: str | None
    is_confirmed: bool


class ManualExecutionResponse(ApiSchema):
    execution_id: int
    execution_status: str
    created_transaction_id: int | None
    linked_ticket_id: int | None
    execution: ManualExecutionSchema
    linked_ticket: OrderTicketSchema | None
    provisional_transaction: ProvisionalTransactionSchema | None
    pending_reconciliation: bool
    transaction_is_confirmed: bool | None
    reconciliation_evidence: ReconciliationEvidenceSchema | None
    confirmation_eligible: bool
    confirmation_blocked_reason: str | None
    available_actions: list[str]
    blocked_actions: list[str]
    explanation: str


class ConfirmExecutionsRequest(ApiSchema):
    reconciliation_id: int | None = None
    account_id: int | None = None
    as_of_date: date | None = None
    execution_ids: list[int] | None = None


class SkippedExecutionSchema(ApiSchema):
    execution_id: int | None
    reason: str
    detail: str | None = None


class ConfirmExecutionsResponse(ApiSchema):
    confirmation_run_id: str
    reconciliation_id_used: int
    total_pending_checked: int
    confirmed_execution_ids: list[int]
    still_pending_execution_ids: list[int]
    failed_execution_ids: list[int]
    skipped_executions: list[SkippedExecutionSchema]
    explanation: str
