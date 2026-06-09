CREATE TABLE IF NOT EXISTS senior_memo_input_bundles (
    input_bundle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    ledger_status TEXT NOT NULL CHECK(ledger_status IN ('reconciled','provisional','stale','broken')),
    latest_reconciliation_id INTEGER REFERENCES reconciliation_snapshots(reconciliation_id),
    portfolio_only INTEGER NOT NULL DEFAULT 0 CHECK(portfolio_only IN (0,1)),
    research_packet_ids_json TEXT NOT NULL DEFAULT '[]',
    macro_context_packet_id INTEGER REFERENCES macro_context_packets(macro_context_packet_id),
    risk_validation_ids_json TEXT NOT NULL DEFAULT '[]',
    order_ticket_ids_json TEXT NOT NULL DEFAULT '[]',
    manual_execution_ids_json TEXT NOT NULL DEFAULT '[]',
    override_ticket_ids_json TEXT NOT NULL DEFAULT '[]',
    decision_journal_ids_json TEXT NOT NULL DEFAULT '[]',
    input_digest TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
