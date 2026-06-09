from __future__ import annotations

from decimal import Decimal


def validate_intent_amounts(requested_quantity: Decimal | None, requested_notional: Decimal | None) -> None:
    if requested_quantity is None and requested_notional is None:
        raise ValueError("requested_quantity or requested_notional is required")
    if requested_quantity is not None and requested_quantity < 0:
        raise ValueError("requested_quantity cannot be negative")
    if requested_notional is not None and requested_notional < 0:
        raise ValueError("requested_notional cannot be negative")
