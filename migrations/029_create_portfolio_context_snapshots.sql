CREATE TABLE IF NOT EXISTS portfolio_context_snapshots (
    portfolio_context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    ledger_status TEXT NOT NULL CHECK(ledger_status IN ('reconciled','provisional','stale','broken')),
    latest_reconciliation_id INTEGER REFERENCES reconciliation_snapshots(reconciliation_id),
    open_ticket_count INTEGER NOT NULL DEFAULT 0,
    pending_execution_count INTEGER NOT NULL DEFAULT 0,
    open_override_count INTEGER NOT NULL DEFAULT 0,
    active_instrument_count INTEGER NOT NULL DEFAULT 0,
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
