from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from portfolio_os.models import CashBalance, Transaction
from portfolio_os.validators import ValidationError, validate_cash_balance, validate_transaction


def base_transaction(transaction_type: str = "buy") -> Transaction:
    return Transaction(
        transaction_id=0,
        account_id=1,
        instrument_id=1 if transaction_type in {"buy", "sell"} else None,
        transaction_type=transaction_type,
        trade_date=date(2026, 1, 2),
        settlement_date=None,
        currency="USD",
        quantity=Decimal("1") if transaction_type == "buy" else Decimal("-1") if transaction_type == "sell" else None,
        price=Decimal("100") if transaction_type in {"buy", "sell"} else None,
        gross_amount=Decimal("100"),
        fee_amount=Decimal("0"),
        tax_amount=Decimal("0"),
        net_cash_amount=Decimal("-100") if transaction_type == "buy" else Decimal("100") if transaction_type == "sell" else Decimal("100"),
        fx_rate_to_base=None,
        source="manual",
        external_ref=None,
        description=None,
        is_confirmed=False,
        is_voided=False,
        void_reason=None,
    )


def test_buy_and_sell_cash_signs_are_enforced() -> None:
    validate_transaction(base_transaction("buy"))
    validate_transaction(base_transaction("sell"))
    bad_buy = base_transaction("buy")
    bad_buy = bad_buy.__class__(**{**bad_buy.__dict__, "net_cash_amount": Decimal("100")})
    with pytest.raises(ValidationError):
        validate_transaction(bad_buy)


def test_negative_fee_or_tax_is_rejected() -> None:
    tx = base_transaction("buy")
    tx = tx.__class__(**{**tx.__dict__, "fee_amount": Decimal("-1")})
    with pytest.raises(ValidationError):
        validate_transaction(tx)


def test_external_snapshot_cash_balance_is_rejected() -> None:
    balance = CashBalance(0, 1, date(2026, 1, 1), "USD", Decimal("100"), "external_snapshot", None, False, None)
    with pytest.raises(ValidationError):
        validate_cash_balance(balance)
