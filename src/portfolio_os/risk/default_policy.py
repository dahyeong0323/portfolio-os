from __future__ import annotations

from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import RiskRule
from portfolio_os.risk.repositories import RiskPolicyRepository


DEFAULT_RULES: tuple[tuple[str, str, str, Decimal, str, str], ...] = (
    ("MIN_CASH_RESERVE", "global", "amount", Decimal("1000"), "adjust_down", "Minimum cash reserve in base currency"),
    ("DAILY_BUY_LIMIT", "global", "amount", Decimal("1000"), "adjust_down", "Daily buy limit in base currency"),
    ("WEEKLY_BUY_LIMIT", "global", "amount", Decimal("3000"), "adjust_down", "Weekly buy limit in base currency"),
    ("MAX_ORDER_NOTIONAL", "global", "amount", Decimal("1000"), "adjust_down", "Single order notional limit in base currency"),
    ("MAX_ASSET_WEIGHT", "global", "ratio", Decimal("0.25"), "adjust_down", "Maximum post-trade asset weight"),
    ("MAX_BUCKET_WEIGHT", "global", "ratio", Decimal("0.50"), "adjust_down", "Maximum post-trade bucket weight"),
    ("TAX_RESERVE_PROTECTION", "global", "ratio", Decimal("1.00"), "hard_block", "Tax reserve cash must be fully protected"),
    ("DEBT_EXPOSURE_CHECK", "global", "ratio", Decimal("0.50"), "hard_block", "total_active_liabilities / gross_portfolio_value <= threshold"),
)


def seed_default_risk_policy(db: Database, base_currency: str, policy_name: str = "stage2_default_policy", version: str = "v1.0.0") -> int:
    repo = RiskPolicyRepository(db)
    existing = db.fetch_one("SELECT * FROM risk_policy_versions WHERE policy_name = ? AND version = ?", (policy_name, version))
    if existing:
        db.execute("UPDATE risk_policy_versions SET is_active = 0 WHERE is_active = 1")
        db.execute("UPDATE risk_policy_versions SET is_active = 1 WHERE policy_version_id = ?", (existing["policy_version_id"],))
        db.commit()
        return existing["policy_version_id"]
    policy = repo.create_policy(
        policy_name=policy_name,
        version=version,
        base_currency=base_currency,
        is_active=True,
        description="Conservative local MVP sample thresholds; not investment advice.",
    )
    for code, scope, unit, value, severity, description in DEFAULT_RULES:
        repo.add_rule(
            RiskRule(
                risk_rule_id=0,
                policy_version_id=policy.policy_version_id,
                rule_code=code,
                rule_scope=scope,
                threshold_value=value,
                threshold_unit=unit,
                currency=base_currency if unit == "amount" else None,
                severity=severity,
                description=description,
            )
        )
    return policy.policy_version_id
