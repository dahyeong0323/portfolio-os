CREATE TABLE IF NOT EXISTS opposing_arguments (
    opposing_argument_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    argument_text TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
