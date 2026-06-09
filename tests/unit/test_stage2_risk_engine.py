from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import LedgerCash, LedgerPosition, LedgerSnapshot
from portfolio_os.risk import RiskEngine, seed_default_risk_policy
from portfolio_os.risk.models import TransactionIntent
from portfolio_os.risk.repositories import PricingRepository
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_cash_anchor, seed_instrument


def intent(account_id: int, instrument_id: int, side: str = "buy", notional: str = "100") -> TransactionIntent:
    return TransactionIntent(
        1,
        account_id,
        instrument_id,
        side,
        "manual",
        Decimal("1"),
        Decimal(notional),
        Decimal("100"),
        "USD",
        "limit",
        None,
        "drafted",
        None,
        None,
        None,
    )


def test_default_policy_uses_requested_base_currency_and_tax_rule(db) -> None:
    policy_id = seed_default_risk_policy(db, "CHF")
    policy = db.fetch_one("SELECT * FROM risk_policy_versions WHERE policy_version_id = ?", (policy_id,))
    assert policy["base_currency"] == "CHF"
    tax_rule = db.fetch_one("SELECT * FROM risk_rules WHERE rule_code = 'TAX_RESERVE_PROTECTION'")
    assert tax_rule["threshold_value"] == "1.00"


def test_buy_requires_reconciled_ledger_but_stale_sell_warns(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 3), "USD", Decimal("100"))
    stale_buy_snapshot = LedgerSnapshot(date(2026, 1, 3), "stale", (), (LedgerCash(account_id, "USD", Decimal("10000")),), (), (), utc_now())
    buy_result = RiskEngine(db).validate_intent(intent(account_id, instrument_id, "buy"), stale_buy_snapshot)
    assert buy_result.validation_status == "rejected"

    stale_sell_snapshot = LedgerSnapshot(
        date(2026, 1, 3),
        "stale",
        (LedgerPosition(account_id, instrument_id, "AAPL", "USD", Decimal("2"), None),),
        (LedgerCash(account_id, "USD", Decimal("10000")),),
        (),
        (),
        utc_now(),
    )
    sell_result = RiskEngine(db).validate_intent(intent(account_id, instrument_id, "sell"), stale_sell_snapshot)
    assert sell_result.validation_status == "passed"
    assert any("LEDGER_STATUS_GATE" in warning for warning in sell_result.warnings)


def test_tax_reserve_and_debt_exposure_checks(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 3), "USD", Decimal("100"))
    snapshot = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id)
    # No reconciled ledger means buy is rejected by non-adjustable gate.
    result = RiskEngine(db).validate_intent(intent(account_id, instrument_id, "buy"), snapshot)
    assert result.validation_status == "rejected"
