from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from portfolio_os.api.schemas import ApiSchema

LedgerStatus = Literal["reconciled", "provisional", "stale", "broken"]


class LedgerStatusResponse(ApiSchema):
    ledger_status: LedgerStatus
    last_reconciled_at: datetime | None
    is_reconciled: bool
    is_provisional: bool
    is_stale: bool
    is_broken: bool
    explanation: str


class LedgerPositionSchema(ApiSchema):
    account_id: int
    instrument_id: int
    symbol: str
    currency: str
    quantity: Decimal
    average_cost: Decimal | None


class LedgerCashSchema(ApiSchema):
    account_id: int
    currency: str
    amount: Decimal


class LedgerLiabilitySchema(ApiSchema):
    liability_id: int
    account_id: int | None
    liability_name: str
    liability_type: str
    currency: str
    current_amount: Decimal


class LedgerTaxReserveSchema(ApiSchema):
    tax_reserve_id: int
    account_id: int | None
    tax_year: int
    tax_type: str
    currency: str
    reserved_amount: Decimal


class LedgerSnapshotResponse(ApiSchema):
    as_of_date: date
    positions: list[LedgerPositionSchema]
    cash: list[LedgerCashSchema]
    liabilities: list[LedgerLiabilitySchema]
    tax_reserves: list[LedgerTaxReserveSchema]
    generated_at: datetime
    ledger_status: LedgerStatus
