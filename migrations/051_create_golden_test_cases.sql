CREATE TABLE IF NOT EXISTS golden_test_cases (
    golden_test_case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    golden_test_set_id INTEGER NOT NULL REFERENCES golden_test_sets(golden_test_set_id),
    case_name TEXT NOT NULL,
    case_type TEXT NOT NULL CHECK(case_type IN ('forbidden_authority_language','valid_context_boundary','read_only_integration','template_activation','custom')),
    input_text TEXT NOT NULL,
    expected_status TEXT NOT NULL CHECK(expected_status IN ('passed','failed','warning')),
    expected_reason TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(golden_test_set_id, case_name)
);
