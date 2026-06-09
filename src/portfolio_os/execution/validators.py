from __future__ import annotations

from decimal import Decimal


def validate_execution_sign(side: str, net_cash_amount: Decimal) -> None:
    if side == "buy" and net_cash_amount >= 0:
        raise ValueError("buy execution net cash must be negative")
    if side == "sell" and net_cash_amount <= 0:
        raise ValueError("sell execution net cash must be positive")
