from __future__ import annotations

from decimal import Decimal

import pytest

from portfolio_os.validators import DecimalValidationError, decimal_to_text, ensure_decimal


def test_decimal_policy_rejects_float() -> None:
    with pytest.raises(DecimalValidationError):
        ensure_decimal(123.45, "money")


def test_decimal_policy_accepts_decimal_string_and_integer() -> None:
    assert ensure_decimal(Decimal("123.45")) == Decimal("123.45")
    assert ensure_decimal("123.45") == Decimal("123.45")
    assert ensure_decimal(123) == Decimal("123")
    assert decimal_to_text(Decimal("123.4500")) == "123.4500"
