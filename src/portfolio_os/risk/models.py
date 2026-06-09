from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

CurrencyCode = str
LedgerStatus = Literal["reconciled", "provisional", "stale", "broken"]
IntentType = Literal["buy", "sell"]
RiskValidationStatus = Literal["passed", "rejected", "adjusted"]
ActionClass = Literal["risk_increasing", "risk_reducing", "correction", "override_precheck"]
IntentStatus = Literal["drafted", "submitted", "risk_passed", "risk_adjusted", "risk_rejected", "ticket_created", "cancelled", "superseded"]
OrderTicketStatus = Literal["validated", "approved", "rejected", "modified", "expired", "executed_provisional", "reconciled", "broken", "cancelled"]
ManualExecutionStatus = Literal["logged", "transaction_created", "pending_reconciliation", "reconciled", "reconciliation_failed", "voided"]
OverrideStatus = Literal["declared", "risk_warned", "human_confirmed", "cancelled", "executed_provisional", "reconciled", "postmortem_due", "postmortem_completed"]


@dataclass(frozen=True)
class PriceSnapshot:
    price_snapshot_id: int
    instrument_id: int
    price_date: date
    price_timestamp: datetime | None
    currency: CurrencyCode
    price: Decimal
    source: str
    source_ref: str | None
    is_active: bool
    notes: str | None


@dataclass(frozen=True)
class FxRate:
    fx_rate_id: int
    rate_date: date
    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    rate: Decimal
    source: str
    source_ref: str | None
    is_active: bool


@dataclass(frozen=True)
class InstrumentRiskProfile:
    risk_profile_id: int
    instrument_id: int
    risk_bucket: str
    is_leveraged: bool
    is_crypto_related: bool
    is_single_name_equity: bool
    max_asset_weight_override: Decimal | None
    max_order_notional_override: Decimal | None
    is_active: bool
    notes: str | None


@dataclass(frozen=True)
class RiskPolicyVersion:
    policy_version_id: int
    policy_name: str
    version: str
    base_currency: CurrencyCode
    is_active: bool
    description: str | None


@dataclass(frozen=True)
class RiskRule:
    risk_rule_id: int
    policy_version_id: int
    rule_code: str
    rule_scope: str
    threshold_value: Decimal
    threshold_unit: str
    severity: str
    currency: CurrencyCode | None
    account_id: int | None = None
    instrument_id: int | None = None
    risk_bucket: str | None = None
    is_active: bool = True
    description: str | None = None


@dataclass(frozen=True)
class TransactionIntent:
    intent_id: int
    account_id: int
    instrument_id: int
    intent_type: IntentType
    intent_source: str
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    limit_price: Decimal | None
    currency: CurrencyCode
    order_type: Literal["limit"]
    rationale: str | None
    status: IntentStatus
    created_at: datetime | None
    updated_at: datetime | None
    expires_at: datetime | None


@dataclass(frozen=True)
class RiskCheckResult:
    check_code: str
    status: Literal["passed", "failed", "adjusted", "warning"]
    message: str
    threshold_value: Decimal | None
    observed_value: Decimal | None
    adjusted_value: Decimal | None


@dataclass(frozen=True)
class RiskValidationResult:
    risk_validation_id: int | None
    intent_id: int
    policy_version_id: int
    reconciliation_id: int | None
    ledger_status_at_validation: LedgerStatus
    ledger_snapshot_as_of: date
    ledger_snapshot_digest: str | None
    validation_status: RiskValidationStatus
    action_class: ActionClass
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    approved_quantity: Decimal | None
    approved_notional: Decimal | None
    max_allowed_notional: Decimal | None
    currency: CurrencyCode
    cash_before: Decimal | None
    cash_after: Decimal | None
    tax_reserve_required: Decimal | None
    checks: tuple[RiskCheckResult, ...]
    failure_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at: datetime | None
    expires_at: datetime | None
    is_superseded: bool


@dataclass(frozen=True)
class OrderTicket:
    order_ticket_id: int
    intent_id: int
    risk_validation_id: int
    account_id: int
    instrument_id: int
    side: IntentType
    order_type: Literal["limit"]
    ticket_quantity: Decimal
    limit_price: Decimal | None
    ticket_notional: Decimal
    currency: CurrencyCode
    status: OrderTicketStatus
    human_decision: str | None
    human_decision_reason: str | None
    approved_at: datetime | None
    rejected_at: datetime | None
    expires_at: datetime
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class ManualExecutionLog:
    manual_execution_id: int
    order_ticket_id: int | None
    override_ticket_id: int | None
    created_transaction_id: int | None
    account_id: int
    instrument_id: int
    side: IntentType
    executed_quantity: Decimal
    executed_price: Decimal
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    currency: CurrencyCode
    executed_at: datetime
    broker_execution_ref: str | None
    execution_status: ManualExecutionStatus
    reconciliation_deadline: date | None
    reconciled_at: datetime | None
    reconciliation_id: int | None
    notes: str | None


@dataclass(frozen=True)
class OverrideTicket:
    override_ticket_id: int
    override_type: str
    account_id: int
    instrument_id: int | None
    side: IntentType | None
    requested_quantity: Decimal | None
    requested_notional: Decimal | None
    currency: CurrencyCode | None
    ledger_status_at_declaration: LedgerStatus
    risk_warning: str
    max_suggested_notional: Decimal | None
    human_reason: str
    human_final_choice: str | None
    status: OverrideStatus
    mandatory_reconciliation_deadline: date | None
    mandatory_postmortem_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
