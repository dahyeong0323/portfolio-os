from __future__ import annotations

from decimal import Decimal

from portfolio_os.models import LedgerSnapshot
from portfolio_os.risk.models import ActionClass, TransactionIntent


def classify_action(intent: TransactionIntent, ledger_snapshot: LedgerSnapshot) -> ActionClass:
    if intent.intent_source == "correction":
        return "correction"
    if intent.intent_source == "override_precheck":
        return "override_precheck"
    if intent.intent_type == "buy":
        return "risk_increasing"
    holding = next(
        (position.quantity for position in ledger_snapshot.positions if position.account_id == intent.account_id and position.instrument_id == intent.instrument_id),
        Decimal("0"),
    )
    if holding > 0:
        return "risk_reducing"
    return "risk_reducing"
