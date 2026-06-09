CREATE TABLE IF NOT EXISTS decision_change_triggers (
    change_trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    trigger_text TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('price','fundamental','macro','risk','ledger','tax','execution','research_missing_data','other')),
    monitoring_note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
