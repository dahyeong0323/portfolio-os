CREATE TABLE IF NOT EXISTS decision_candidates (
    decision_candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    senior_memo_id INTEGER NOT NULL REFERENCES senior_memos(senior_memo_id),
    instrument_id INTEGER REFERENCES instruments(instrument_id),
    candidate_type TEXT NOT NULL CHECK(candidate_type IN (
        'no_action','review','create_intent_candidate','reduce_risk_candidate','watchlist_update','research_needed','correction_review'
    )),
    candidate_action_class TEXT NOT NULL CHECK(candidate_action_class IN ('review_only','risk_increasing','risk_reducing','correction')),
    candidate_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    required_next_step TEXT NOT NULL CHECK(required_next_step IN (
        'none','human_review','stage2_create_intent','stage2_risk_validation','additional_research','reconciliation_required','correction_required'
    )),
    candidate_status TEXT NOT NULL DEFAULT 'draft' CHECK(candidate_status IN (
        'draft','valid','blocked_pending_reconciliation','blocked_pending_risk_validation','archived'
    )),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high')),
    risk_validation_required INTEGER NOT NULL DEFAULT 0 CHECK(risk_validation_required IN (0,1)),
    reconciliation_required_first INTEGER NOT NULL DEFAULT 0 CHECK(reconciliation_required_first IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
