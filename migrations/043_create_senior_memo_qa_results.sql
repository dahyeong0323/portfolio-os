CREATE TABLE IF NOT EXISTS senior_memo_qa_results (
    senior_memo_qa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    qa_status TEXT NOT NULL CHECK(qa_status IN ('passed','failed')),
    required_section_count INTEGER NOT NULL DEFAULT 0,
    missing_required_sections_json TEXT NOT NULL DEFAULT '[]',
    candidate_count INTEGER NOT NULL DEFAULT 0,
    no_action_count INTEGER NOT NULL DEFAULT 0,
    opposing_argument_count INTEGER NOT NULL DEFAULT 0,
    change_trigger_count INTEGER NOT NULL DEFAULT 0,
    invalid_input_count INTEGER NOT NULL DEFAULT 0,
    forbidden_language_count INTEGER NOT NULL DEFAULT 0,
    failure_reasons_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
