CREATE TABLE IF NOT EXISTS configuration_snapshots (
    configuration_snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_name TEXT NOT NULL,
    snapshot_scope TEXT NOT NULL DEFAULT 'system' CHECK(snapshot_scope IN ('system','governance','context','template','integration','health')),
    as_of_date TEXT NOT NULL,
    stage_versions_json TEXT NOT NULL DEFAULT '{}',
    active_risk_policy_id INTEGER REFERENCES risk_policy_versions(policy_version_id),
    active_governance_policy_id INTEGER REFERENCES governance_policies(governance_policy_id),
    active_template_version_ids_json TEXT NOT NULL DEFAULT '[]',
    configuration_json TEXT NOT NULL DEFAULT '{}',
    snapshot_digest TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
