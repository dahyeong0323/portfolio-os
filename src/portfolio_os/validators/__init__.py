from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from portfolio_os.models import (
    Account,
    CashBalance,
    ExternalAccountSnapshot,
    Instrument,
    Liability,
    TaxReserve,
    Transaction,
)


class ValidationError(Exception):
    pass


class IntegrityValidationError(ValidationError):
    pass


class DecimalValidationError(ValidationError):
    pass


class ReferenceValidationError(ValidationError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def datetime_to_text(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def datetime_from_text(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def date_to_text(value: date) -> str:
    return value.isoformat()


def date_from_text(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def ensure_decimal(value: Any, field_name: str = "value", allow_none: bool = False) -> Decimal | None:
    if value is None:
        if allow_none:
            return None
        raise DecimalValidationError(f"{field_name} is required")
    if isinstance(value, bool) or isinstance(value, float):
        raise DecimalValidationError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise DecimalValidationError(f"{field_name} is not a valid decimal: {value}") from exc
    raise DecimalValidationError(f"{field_name} must be Decimal, string, or integer")


def decimal_to_text(value: Any, field_name: str = "value", allow_none: bool = False) -> str | None:
    decimal_value = ensure_decimal(value, field_name, allow_none=allow_none)
    if decimal_value is None:
        return None
    return format(decimal_value, "f")


def decimal_from_text(value: str | None, field_name: str = "value", allow_none: bool = False) -> Decimal | None:
    if value is None:
        if allow_none:
            return None
        raise DecimalValidationError(f"{field_name} is required")
    return ensure_decimal(value, field_name)


def validate_currency_code(currency: str) -> None:
    if len(currency) != 3 or currency.upper() != currency or not currency.isalpha():
        raise ValidationError(f"currency must be a 3-letter uppercase code: {currency}")


def require_text(value: str | None, field_name: str) -> None:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} is required")


def validate_account(account: Account) -> None:
    require_text(account.account_name, "account_name")
    require_text(account.institution_name, "institution_name")
    validate_currency_code(account.base_currency)
    if account.closed_date and account.opened_date and account.closed_date < account.opened_date:
        raise ValidationError("closed_date cannot be earlier than opened_date")


def validate_instrument(instrument: Instrument) -> None:
    require_text(instrument.symbol, "symbol")
    require_text(instrument.instrument_name, "instrument_name")
    validate_currency_code(instrument.currency)
    if instrument.quantity_precision < 0 or instrument.price_precision < 0:
        raise ValidationError("precision values cannot be negative")


def validate_transaction(transaction: Transaction) -> None:
    validate_currency_code(transaction.currency)
    ensure_decimal(transaction.gross_amount, "gross_amount")
    fee = ensure_decimal(transaction.fee_amount, "fee_amount")
    tax = ensure_decimal(transaction.tax_amount, "tax_amount")
    net = ensure_decimal(transaction.net_cash_amount, "net_cash_amount")
    if fee < 0:
        raise ValidationError("fee_amount cannot be negative")
    if tax < 0:
        raise ValidationError("tax_amount cannot be negative")
    if transaction.fx_rate_to_base is not None:
        ensure_decimal(transaction.fx_rate_to_base, "fx_rate_to_base")
    if transaction.transaction_type in {"buy", "sell"}:
        if transaction.instrument_id is None or transaction.quantity is None or transaction.price is None:
            raise ValidationError("buy/sell require instrument_id, quantity, and price")
        quantity = ensure_decimal(transaction.quantity, "quantity")
        price = ensure_decimal(transaction.price, "price")
        if price <= 0:
            raise ValidationError("price must be positive for buy/sell")
        if transaction.transaction_type == "buy":
            if quantity <= 0:
                raise ValidationError("buy quantity must be positive")
            if net >= 0:
                raise ValidationError("buy net_cash_amount must be negative")
        if transaction.transaction_type == "sell":
            if quantity >= 0:
                raise ValidationError("sell quantity must be negative")
            if net <= 0:
                raise ValidationError("sell net_cash_amount must be positive")
    elif transaction.quantity is not None or transaction.price is not None:
        ensure_decimal(transaction.quantity, "quantity")
        ensure_decimal(transaction.price, "price")
    if transaction.transaction_type in {"withdrawal", "fee", "tax", "transfer_out"} and net > 0:
        raise ValidationError(f"{transaction.transaction_type} net_cash_amount must not be positive")
    if transaction.transaction_type in {"deposit", "dividend", "interest", "transfer_in"} and net < 0:
        raise ValidationError(f"{transaction.transaction_type} net_cash_amount must not be negative")
    if transaction.is_voided and not transaction.void_reason:
        raise ValidationError("void_reason is required for voided transactions")
    if transaction.transaction_type in {"reversal", "correction"} and not transaction.description:
        raise ValidationError("reversal/correction require original transaction reference in description")


def validate_cash_balance(cash_balance: CashBalance) -> None:
    validate_currency_code(cash_balance.currency)
    ensure_decimal(cash_balance.amount, "amount")
    if cash_balance.source == "external_snapshot":
        raise ValidationError("external snapshots must not be inserted into cash_balances")


def validate_liability(liability: Liability) -> None:
    require_text(liability.liability_name, "liability_name")
    validate_currency_code(liability.currency)
    amount = ensure_decimal(liability.current_amount, "current_amount")
    if amount < 0:
        raise ValidationError("current_amount cannot be negative")
    if not liability.is_active and amount != 0:
        raise ValidationError("inactive liabilities must have current_amount = 0")
    if liability.principal_amount is not None:
        ensure_decimal(liability.principal_amount, "principal_amount")
    if liability.interest_rate_annual is not None:
        ensure_decimal(liability.interest_rate_annual, "interest_rate_annual")
    if liability.due_date and liability.due_date < liability.as_of_date:
        raise ValidationError("due_date cannot be earlier than as_of_date")


def validate_tax_reserve(tax_reserve: TaxReserve) -> None:
    validate_currency_code(tax_reserve.currency)
    if tax_reserve.tax_year < 2000:
        raise ValidationError("tax_year must be 2000 or later")
    amount = ensure_decimal(tax_reserve.reserved_amount, "reserved_amount")
    if amount < 0:
        raise ValidationError("reserved_amount cannot be negative")


def validate_external_snapshot(snapshot: ExternalAccountSnapshot) -> None:
    for position in snapshot.positions:
        validate_currency_code(position.currency)
        ensure_decimal(position.quantity, "position.quantity")
    for cash in snapshot.cash:
        validate_currency_code(cash.currency)
        ensure_decimal(cash.amount, "cash.amount")
    for liability in snapshot.liabilities:
        validate_currency_code(liability.currency)
        ensure_decimal(liability.current_amount, "liability.current_amount")
    for reserve in snapshot.tax_reserves:
        validate_currency_code(reserve.currency)
        ensure_decimal(reserve.reserved_amount, "tax_reserve.reserved_amount")
