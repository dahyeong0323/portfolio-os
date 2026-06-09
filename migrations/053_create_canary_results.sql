CREATE TABLE IF NOT EXISTS canary_results (
    canary_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canary_run_id INTEGER NOT NULL REFERENCES canary_runs(canary_run_id),
    golden_test_case_id INTEGER REFERENCES golden_test_cases(golden_test_case_id),
    check_code TEXT NOT NULL,
    result_status TEXT NOT NULL CHECK(result_status IN ('passed','failed','warning')),
    severity TEXT NOT NULL DEFAULT 'hard_block' CHECK(severity IN ('info','warning','hard_block')),
    result_summary TEXT NOT NULL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
