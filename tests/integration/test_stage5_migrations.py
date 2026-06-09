from __future__ import annotations


def test_stage5_migrations_apply_after_stage1_to_stage4(db) -> None:
    expected_tables = {
        "governance_policies",
        "governance_policy_rules",
        "configuration_snapshots",
        "template_registry",
        "template_versions",
        "golden_test_sets",
        "golden_test_cases",
        "canary_runs",
        "canary_results",
        "context_packages",
        "context_package_items",
        "context_budget_records",
        "delta_reviews",
        "memory_items",
        "system_health_snapshots",
        "read_only_integration_sources",
        "read_only_import_runs",
        "governance_audit_events",
    }
    tables = {row["name"] for row in db.fetch_all("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert expected_tables <= tables
    latest = db.fetch_one("SELECT MAX(version) AS version FROM schema_migrations")
    versions = [row["version"] for row in db.fetch_all("SELECT version FROM schema_migrations ORDER BY version")]
    assert 63 in versions
    assert latest["version"] == 63
