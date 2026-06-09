CREATE TABLE IF NOT EXISTS governance_audit_events (
    governance_audit_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_scope TEXT NOT NULL DEFAULT 'system',
    severity TEXT NOT NULL DEFAULT 'info' CHECK(severity IN ('info','warning','hard_block')),
    related_table TEXT,
    related_id INTEGER,
    event_summary TEXT NOT NULL,
    event_payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
