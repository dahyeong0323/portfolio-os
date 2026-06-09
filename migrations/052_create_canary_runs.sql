CREATE TABLE IF NOT EXISTS canary_runs (
    canary_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_scope TEXT NOT NULL DEFAULT 'system' CHECK(run_scope IN ('system','authority_boundary','template','context','integration')),
    run_status TEXT NOT NULL DEFAULT 'running' CHECK(run_status IN ('running','passed','failed')),
    governance_policy_id INTEGER REFERENCES governance_policies(governance_policy_id),
    configuration_snapshot_id INTEGER REFERENCES configuration_snapshots(configuration_snapshot_id),
    golden_test_set_ids_json TEXT NOT NULL DEFAULT '[]',
    passed_count INTEGER NOT NULL DEFAULT 0 CHECK(passed_count >= 0),
    failed_count INTEGER NOT NULL DEFAULT 0 CHECK(failed_count >= 0),
    warning_count INTEGER NOT NULL DEFAULT 0 CHECK(warning_count >= 0),
    summary_text TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    completed_at TEXT
);
