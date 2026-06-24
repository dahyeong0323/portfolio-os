from datetime import date, datetime
from decimal import Decimal

from portfolio_os.api.schemas import ApiSchema
from portfolio_os.api.schemas.journal import DecisionJournalEntrySchema
from portfolio_os.api.schemas.postmortems import PostmortemTaskSchema


class OverrideTicketSchema(ApiSchema):
    override_id: int
    status: str
    override_type: str
    account_id: int
    account_name: str | None = None
    instrument_id: int | None
    instrument_symbol: str | None = None
    instrument_name: str | None = None
    side: str | None
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    currency: str | None
    human_reason: str
    human_final_choice: str | None
    risk_warning: str
    ledger_status_at_declaration: str
    mandatory_reconciliation_deadline: date | None
    mandatory_postmortem_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    linked_postmortem_task_id: int | None
    available_actions: list[str]
    blocked_actions: list[str]


class OverrideListResponse(ApiSchema):
    count: int
    open_count: int
    overrides: list[OverrideTicketSchema]


class DeclareOverrideRequest(ApiSchema):
    override_type: str
    account_id: int
    instrument_id: int | None = None
    side: str | None = None
    requested_quantity: Decimal | None = None
    requested_notional: Decimal | None = None
    currency: str | None = None
    human_reason: str
    emotional_state: str | None = None


class OverrideActionRequest(ApiSchema):
    emotional_state: str | None = None


class OverrideResponse(ApiSchema):
    override: OverrideTicketSchema
    linked_journal_entries: list[DecisionJournalEntrySchema]
    postmortem_task: PostmortemTaskSchema | None
    explanation: str
