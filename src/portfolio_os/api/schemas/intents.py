from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from portfolio_os.api.schemas import ApiSchema


IntentSide = Literal["buy", "sell"]
IntentStatus = Literal[
    "drafted",
    "submitted",
    "risk_passed",
    "risk_adjusted",
    "risk_rejected",
    "ticket_created",
    "cancelled",
    "superseded",
]


class CreateIntentRequest(ApiSchema):
    account_id: int = Field(gt=0)
    instrument_id: int = Field(gt=0)
    side: IntentSide
    currency: str = Field(min_length=3, max_length=3)
    requested_quantity: Decimal | None = Field(default=None, ge=0)
    requested_notional: Decimal | None = Field(default=None, ge=0)
    limit_price: Decimal | None = Field(default=None, ge=0)
    rationale: str | None = Field(default=None, max_length=1000)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def require_amount(self) -> "CreateIntentRequest":
        if self.requested_quantity is None and self.requested_notional is None:
            raise ValueError("requested_quantity or requested_notional is required")
        return self


class IntentSchema(ApiSchema):
    intent_id: int
    account_id: int
    instrument_id: int
    intent_type: IntentSide
    intent_source: str
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    limit_price: Decimal | None
    currency: str
    order_type: str
    rationale: str | None
    status: IntentStatus
    created_at: datetime | None
    updated_at: datetime | None
    expires_at: datetime | None


class CreateIntentResponse(ApiSchema):
    intent: IntentSchema
    next_available_actions: list[str]


class ValidateIntentRequest(ApiSchema):
    as_of_date: str | None = None
    policy_version_id: int | None = Field(default=None, gt=0)


class IntentSummarySchema(ApiSchema):
    intent_id: int
    status: IntentStatus
    account_id: int
    instrument_id: int
    side: IntentSide
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    limit_price: Decimal | None
    currency: str
    created_at: datetime | None
