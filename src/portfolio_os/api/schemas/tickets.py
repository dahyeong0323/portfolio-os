from datetime import datetime
from decimal import Decimal

from portfolio_os.api.schemas import ApiSchema
from portfolio_os.api.schemas.intents import IntentSummarySchema
from portfolio_os.api.schemas.risk import RiskValidationSchema


class OrderTicketSchema(ApiSchema):
    order_ticket_id: int
    intent_id: int
    risk_validation_id: int
    account_id: int
    instrument_id: int
    side: str
    order_type: str
    ticket_quantity: Decimal
    limit_price: Decimal | None
    ticket_notional: Decimal
    currency: str
    status: str
    human_decision: str | None
    human_decision_reason: str | None
    approved_at: datetime | None
    rejected_at: datetime | None
    expires_at: datetime
    created_at: datetime | None
    updated_at: datetime | None


class OrderTicketListResponse(ApiSchema):
    count: int
    tickets: list[OrderTicketSchema]


class CreateTicketRequest(ApiSchema):
    risk_validation_id: int
    expires_at: datetime | None = None


class OrderTicketEventSchema(ApiSchema):
    event_id: int
    order_ticket_id: int
    event_type: str
    from_status: str | None
    to_status: str
    event_payload: dict[str, object]
    created_at: datetime | None


class CreateTicketResponse(ApiSchema):
    ticket: OrderTicketSchema
    risk_validation_id: int
    intent_id: int
    available_actions: list[str]
    blocked_actions: list[str]


class TicketDecisionRequest(ApiSchema):
    approval_note: str | None = None
    rejection_reason: str | None = None
    emotional_state: str | None = None


class TicketActionResponse(ApiSchema):
    ticket_id: int
    new_ticket_status: str
    ticket: OrderTicketSchema
    ticket_events: list[OrderTicketEventSchema]
    linked_decision_journal_entry_id: int | None
    available_actions: list[str]
    blocked_actions: list[str]


class OrderTicketDetailResponse(ApiSchema):
    ticket: OrderTicketSchema
    linked_risk_validation: RiskValidationSchema
    linked_intent: IntentSummarySchema
    ticket_events: list[OrderTicketEventSchema]
    available_actions: list[str]
    blocked_actions: list[str]
