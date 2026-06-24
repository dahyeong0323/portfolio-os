from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from portfolio_os.api.schemas import ApiSchema


RiskValidationStatus = Literal["passed", "adjusted", "rejected"]
RiskCheckStatus = Literal["passed", "failed", "adjusted", "warning"]


class RiskCheckSchema(ApiSchema):
    check_code: str
    status: RiskCheckStatus
    message: str
    threshold_value: Decimal | None
    observed_value: Decimal | None
    adjusted_value: Decimal | None


class RiskValidationSchema(ApiSchema):
    risk_validation_id: int | None
    intent_id: int
    policy_version_id: int
    reconciliation_id: int | None
    ledger_status_at_validation: str
    ledger_snapshot_as_of: date
    ledger_snapshot_digest: str | None
    validation_status: RiskValidationStatus
    action_class: str
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    approved_quantity: Decimal | None
    approved_notional: Decimal | None
    max_allowed_notional: Decimal | None
    currency: str
    cash_before: Decimal | None
    cash_after: Decimal | None
    tax_reserve_required: Decimal | None
    checks: list[RiskCheckSchema]
    failure_reasons: list[str]
    warnings: list[str]
    created_at: datetime | None
    expires_at: datetime | None
    is_superseded: bool


class ValidateIntentResponse(ApiSchema):
    validation: RiskValidationSchema
    ledger_status_gate: RiskCheckSchema | None
    failed_checks: list[RiskCheckSchema]
    warnings: list[str]
    explanation: str
    next_available_actions: list[str]


class RiskValidationDetailResponse(ApiSchema):
    validation: RiskValidationSchema
    associated_intent_id: int
    generated_at: datetime | None
