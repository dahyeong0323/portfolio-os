from datetime import date, datetime
from decimal import Decimal

from portfolio_os.api.schemas import ApiSchema
from portfolio_os.api.schemas.ledger import (
    LedgerCashSchema,
    LedgerLiabilitySchema,
    LedgerPositionSchema,
    LedgerTaxReserveSchema,
    LedgerStatus,
)


class ExternalPositionSchema(ApiSchema):
    account_id: int
    symbol: str
    currency: str
    quantity: Decimal
    exchange: str | None = None
    instrument_id: int | None = None
    match_status: str = "matched"
    match_error: str | None = None


class ExternalCashSchema(ApiSchema):
    account_id: int
    currency: str
    amount: Decimal


class ExternalLiabilitySchema(ApiSchema):
    account_id: int | None
    liability_name: str
    currency: str
    current_amount: Decimal
    liability_type: str | None = None


class ExternalTaxReserveSchema(ApiSchema):
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: str
    reserved_amount: Decimal


class PositionDifferenceSchema(ApiSchema):
    account_id: int
    instrument_id: int | None
    symbol: str
    expected_quantity: Decimal
    actual_quantity: Decimal
    difference: Decimal
    within_tolerance: bool


class CashDifferenceSchema(ApiSchema):
    account_id: int
    currency: str
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


class LiabilityDifferenceSchema(ApiSchema):
    account_id: int | None
    liability_name: str
    currency: str
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


class TaxReserveDifferenceSchema(ApiSchema):
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: str
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


class StoredReconciliationToleranceSchema(ApiSchema):
    cash_abs: Decimal
    quantity_abs: Decimal


class ReconciliationSnapshotSchema(ApiSchema):
    reconciliation_id: int
    account_id: int | None
    as_of_date: date
    started_at: datetime
    completed_at: datetime | None
    ledger_status_before: LedgerStatus
    ledger_status_after: LedgerStatus
    reconciliation_status: str
    snapshot_source: str
    position_diff_count: int
    cash_diff_count: int
    liability_diff_count: int
    tax_reserve_diff_count: int
    total_abs_cash_diff_base: Decimal
    tolerance: StoredReconciliationToleranceSchema
    expected_positions: list[LedgerPositionSchema]
    actual_positions: list[ExternalPositionSchema]
    position_differences: list[PositionDifferenceSchema]
    expected_cash: list[LedgerCashSchema]
    actual_cash: list[ExternalCashSchema]
    cash_differences: list[CashDifferenceSchema]
    expected_liabilities: list[LedgerLiabilitySchema]
    actual_liabilities: list[ExternalLiabilitySchema]
    liability_differences: list[LiabilityDifferenceSchema]
    expected_tax_reserves: list[LedgerTaxReserveSchema]
    actual_tax_reserves: list[ExternalTaxReserveSchema]
    tax_reserve_differences: list[TaxReserveDifferenceSchema]
    failure_reason: str | None
    created_at: datetime


class LatestReconciliationResponse(ApiSchema):
    found: bool
    reconciliation: ReconciliationSnapshotSchema | None


class RunReconciliationRequest(ApiSchema):
    artifact_id: str
    account_id: int
    as_of_date: date | None = None


class ReconciliationDiffCountsSchema(ApiSchema):
    positions: int
    cash: int
    liabilities: int
    tax_reserves: int


class RunReconciliationResponse(ApiSchema):
    reconciliation_id: int
    reconciliation_status: str
    ledger_status: LedgerStatus
    generated_at: datetime
    diff_counts: ReconciliationDiffCountsSchema
    report_available: bool
    report_reference: str | None
    explanation: str
    warnings: list[str]


class ReconciliationReportResponse(ApiSchema):
    reconciliation_id: int
    format: str
    content: str
    generated_at: datetime
    report_reference: str
