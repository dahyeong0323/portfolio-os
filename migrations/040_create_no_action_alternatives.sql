CREATE TABLE IF NOT EXISTS no_action_alternatives (
    no_action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    alternative_text TEXT NOT NULL,
    why_reasonable TEXT NOT NULL,
    opportunity_cost TEXT,
    risk_reduction_benefit TEXT,
    review_trigger TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
