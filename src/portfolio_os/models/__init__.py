from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

CurrencyCode = str
LedgerStatus = Literal["reconciled", "provisional", "stale", "broken"]
ReconciliationStatus = Literal["passed", "failed", "needs_review"]
AccountType = Literal["securities", "cash", "savings", "loan", "tax", "other"]
InstrumentType = Literal["stock", "etf", "crypto", "fund", "bond", "cash_equivalent", "other"]
TransactionType = Literal[
    "buy",
    "sell",
    "deposit",
    "withdrawal",
    "dividend",
    "interest",
    "fee",
    "tax",
    "transfer_in",
    "transfer_out",
    "reversal",
    "correction",
]
DataSource = Literal["manual", "csv_import", "external_snapshot", "system_correction"]
SnapshotSource = Literal["manual", "csv_import", "external_statement"]
PositionMatchStatus = Literal["matched", "missing", "ambiguous", "invalid"]


@dataclass(frozen=True)
class Account:
    account_id: int
    account_name: str
    institution_name: str
    account_type: AccountType
    base_currency: CurrencyCode
    account_number_masked: str | None
    is_active: bool
    opened_date: date | None
    closed_date: date | None
    notes: str | None


@dataclass(frozen=True)
class Instrument:
    instrument_id: int
    symbol: str
    instrument_name: str
    instrument_type: InstrumentType
    exchange: str | None
    isin: str | None
    currency: CurrencyCode
    country: str | None
    is_fractional_allowed: bool
    quantity_precision: int
    price_precision: int
    is_active: bool
    notes: str | None


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    account_id: int
    instrument_id: int | None
    transaction_type: TransactionType
    trade_date: date
    settlement_date: date | None
    currency: CurrencyCode
    quantity: Decimal | None
    price: Decimal | None
    gross_amount: Decimal
    fee_amount: Decimal
    tax_amount: Decimal
    net_cash_amount: Decimal
    fx_rate_to_base: Decimal | None
    source: DataSource
    external_ref: str | None
    description: str | None
    is_confirmed: bool
    is_voided: bool
    void_reason: str | None


@dataclass(frozen=True)
class CashBalance:
    cash_balance_id: int
    account_id: int
    as_of_date: date
    currency: CurrencyCode
    amount: Decimal
    source: DataSource
    external_ref: str | None
    is_reconciled: bool
    notes: str | None


@dataclass(frozen=True)
class Liability:
    liability_id: int
    account_id: int | None
    liability_name: str
    liability_type: str
    currency: CurrencyCode
    principal_amount: Decimal | None
    current_amount: Decimal
    interest_rate_annual: Decimal | None
    as_of_date: date
    due_date: date | None
    source: DataSource
    is_active: bool
    notes: str | None


@dataclass(frozen=True)
class TaxReserve:
    tax_reserve_id: int
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal
    as_of_date: date
    source: DataSource
    calculation_basis: str | None
    is_active: bool
    notes: str | None


@dataclass(frozen=True)
class LedgerPosition:
    account_id: int
    instrument_id: int
    symbol: str
    currency: CurrencyCode
    quantity: Decimal
    average_cost: Decimal | None


@dataclass(frozen=True)
class LedgerCash:
    account_id: int
    currency: CurrencyCode
    amount: Decimal


@dataclass(frozen=True)
class LedgerLiability:
    liability_id: int
    account_id: int | None
    liability_name: str
    liability_type: str
    currency: CurrencyCode
    current_amount: Decimal


@dataclass(frozen=True)
class LedgerTaxReserve:
    tax_reserve_id: int
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal


@dataclass(frozen=True)
class LedgerSnapshot:
    as_of_date: date
    ledger_status: LedgerStatus
    positions: tuple[LedgerPosition, ...]
    cash: tuple[LedgerCash, ...]
    liabilities: tuple[LedgerLiability, ...]
    tax_reserves: tuple[LedgerTaxReserve, ...]
    generated_at: datetime


@dataclass(frozen=True)
class ExternalPosition:
    account_id: int
    symbol: str
    currency: CurrencyCode
    quantity: Decimal
    exchange: str | None = None
    instrument_id: int | None = None
    match_status: PositionMatchStatus = "matched"
    match_error: str | None = None


@dataclass(frozen=True)
class ExternalCash:
    account_id: int
    currency: CurrencyCode
    amount: Decimal


@dataclass(frozen=True)
class ExternalLiability:
    account_id: int | None
    liability_name: str
    currency: CurrencyCode
    current_amount: Decimal
    liability_type: str | None = None


@dataclass(frozen=True)
class ExternalTaxReserve:
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    reserved_amount: Decimal


@dataclass(frozen=True)
class ExternalAccountSnapshot:
    as_of_date: date
    source: SnapshotSource
    positions: tuple[ExternalPosition, ...]
    cash: tuple[ExternalCash, ...]
    liabilities: tuple[ExternalLiability, ...]
    tax_reserves: tuple[ExternalTaxReserve, ...]
    received_at: datetime


@dataclass(frozen=True)
class ReconciliationTolerance:
    cash_abs: Decimal
    quantity_abs: Decimal
    liability_abs: Decimal
    tax_reserve_abs: Decimal


@dataclass(frozen=True)
class PositionDifference:
    account_id: int
    instrument_id: int | None
    symbol: str
    expected_quantity: Decimal
    actual_quantity: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class CashDifference:
    account_id: int
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class LiabilityDifference:
    account_id: int | None
    liability_name: str
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class TaxReserveDifference:
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: CurrencyCode
    expected_amount: Decimal
    actual_amount: Decimal
    difference: Decimal
    within_tolerance: bool


@dataclass(frozen=True)
class ReconciliationResult:
    reconciliation_id: int | None
    account_id: int | None
    as_of_date: date
    started_at: datetime
    completed_at: datetime
    ledger_status_before: LedgerStatus
    ledger_status_after: LedgerStatus
    reconciliation_status: ReconciliationStatus
    snapshot_source: SnapshotSource
    expected_positions: tuple[LedgerPosition, ...]
    actual_positions: tuple[ExternalPosition, ...]
    position_differences: tuple[PositionDifference, ...]
    expected_cash: tuple[LedgerCash, ...]
    actual_cash: tuple[ExternalCash, ...]
    cash_differences: tuple[CashDifference, ...]
    expected_liabilities: tuple[LedgerLiability, ...]
    actual_liabilities: tuple[ExternalLiability, ...]
    liability_differences: tuple[LiabilityDifference, ...]
    expected_tax_reserves: tuple[LedgerTaxReserve, ...]
    actual_tax_reserves: tuple[ExternalTaxReserve, ...]
    tax_reserve_differences: tuple[TaxReserveDifference, ...]
    tolerance: ReconciliationTolerance
    failure_reason: str | None
