from datetime import datetime
from typing import Any

from portfolio_os.api.schemas import ApiSchema


class DecisionJournalEntrySchema(ApiSchema):
    decision_id: int
    decision_type: str
    order_ticket_id: int | None
    override_ticket_id: int | None
    risk_validation_id: int | None
    manual_execution_id: int | None
    human_decision: str
    reason: str | None
    emotional_state: str | None
    context: dict[str, Any]
    created_at: datetime


class DecisionJournalListResponse(ApiSchema):
    count: int
    entries: list[DecisionJournalEntrySchema]
