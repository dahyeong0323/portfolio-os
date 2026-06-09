CREATE TABLE IF NOT EXISTS senior_memos (
    senior_memo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_bundle_id INTEGER NOT NULL REFERENCES senior_memo_input_bundles(input_bundle_id),
    memo_title TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    memo_status TEXT NOT NULL DEFAULT 'draft' CHECK(memo_status IN ('draft','valid','invalid','archived')),
    memo_scope TEXT NOT NULL CHECK(memo_scope IN ('portfolio','asset','multi_asset')),
    memo_recommendation_scope TEXT NOT NULL DEFAULT 'review_only' CHECK(memo_recommendation_scope IN ('review_only','candidate_actions_require_risk','no_official_action')),
    executive_summary TEXT NOT NULL,
    confidence_level TEXT NOT NULL DEFAULT 'medium' CHECK(confidence_level IN ('low','medium','high')),
    primary_risk_summary TEXT,
    no_action_is_acceptable INTEGER NOT NULL DEFAULT 1 CHECK(no_action_is_acceptable IN (0,1)),
    qa_status TEXT NOT NULL DEFAULT 'not_run' CHECK(qa_status IN ('not_run','passed','failed')),
    created_by TEXT NOT NULL DEFAULT 'human' CHECK(created_by IN ('human','system','import')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
