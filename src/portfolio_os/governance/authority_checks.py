from __future__ import annotations

FORBIDDEN_AUTHORITY_PHRASES: tuple[str, ...] = (
    "execute this order",
    "execute order",
    "place the order",
    "place order",
    "approve ticket",
    "approve the ticket",
    "create order ticket",
    "create a risk validation",
    "risk validation is approved",
    "skip risk validation",
    "bypass risk validation",
    "bypass reconciliation",
    "buy now",
    "sell now",
    "size the trade",
    "authorized to trade",
    "execution authorization",
)


def find_authority_boundary_hits(text: str | None) -> tuple[str, ...]:
    if not text:
        return ()
    lowered = text.lower()
    return tuple(phrase for phrase in FORBIDDEN_AUTHORITY_PHRASES if phrase in lowered)


def evaluate_authority_text(text: str | None) -> str:
    return "failed" if find_authority_boundary_hits(text) else "passed"
