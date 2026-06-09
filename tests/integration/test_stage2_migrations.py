from __future__ import annotations

from portfolio_os.risk import seed_default_risk_policy


def test_stage2_migrations_apply_after_stage1(db) -> None:
    tables = {row["name"] for row in db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in {
        "price_snapshots",
        "fx_rates",
        "instrument_risk_profiles",
        "risk_policy_versions",
        "risk_rules",
        "transaction_intents",
        "risk_validation_results",
        "order_tickets",
        "order_ticket_events",
        "manual_execution_logs",
        "override_tickets",
        "decision_journal",
        "postmortem_tasks",
    }:
        assert table in tables
    versions = [row["version"] for row in db.fetch_all("SELECT version FROM schema_migrations ORDER BY version")]
    assert versions[0] == 1
    assert 22 in versions


def test_seed_default_policy_with_non_usd_base_currency(db) -> None:
    policy_id = seed_default_risk_policy(db, "CHF")
    policy = db.fetch_one("SELECT * FROM risk_policy_versions WHERE policy_version_id = ?", (policy_id,))
    assert policy["base_currency"] == "CHF"
    rule_count = db.fetch_one("SELECT count(*) AS c FROM risk_rules WHERE policy_version_id = ?", (policy_id,))["c"]
    assert rule_count >= 8
