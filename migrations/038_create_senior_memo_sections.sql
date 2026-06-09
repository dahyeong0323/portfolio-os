CREATE TABLE IF NOT EXISTS senior_memo_sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    section_type TEXT NOT NULL CHECK(section_type IN (
        'portfolio_diagnosis','macro_interpretation','cash_liquidity','asset_thesis_status','risk_context',
        'execution_context','no_action_case','opposing_argument','change_triggers','required_risk_validation'
    )),
    section_title TEXT NOT NULL,
    section_text TEXT NOT NULL,
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
