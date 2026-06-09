CREATE TABLE IF NOT EXISTS system_health_snapshots (
    system_health_snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    health_status TEXT NOT NULL CHECK(health_status IN ('green','yellow','red')),
    ledger_status TEXT,
    latest_reconciliation_status TEXT,
    latest_canary_status TEXT,
    open_ticket_count INTEGER NOT NULL DEFAULT 0 CHECK(open_ticket_count >= 0),
    pending_execution_count INTEGER NOT NULL DEFAULT 0 CHECK(pending_execution_count >= 0),
    open_override_count INTEGER NOT NULL DEFAULT 0 CHECK(open_override_count >= 0),
    invalid_research_count INTEGER NOT NULL DEFAULT 0 CHECK(invalid_research_count >= 0),
    invalid_macro_count INTEGER NOT NULL DEFAULT 0 CHECK(invalid_macro_count >= 0),
    invalid_senior_memo_count INTEGER NOT NULL DEFAULT 0 CHECK(invalid_senior_memo_count >= 0),
    warning_count INTEGER NOT NULL DEFAULT 0 CHECK(warning_count >= 0),
    failure_count INTEGER NOT NULL DEFAULT 0 CHECK(failure_count >= 0),
    health_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
