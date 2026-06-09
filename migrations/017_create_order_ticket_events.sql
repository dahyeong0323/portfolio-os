CREATE TABLE IF NOT EXISTS order_ticket_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_ticket_id INTEGER NOT NULL REFERENCES order_tickets(order_ticket_id),
    event_type TEXT NOT NULL CHECK(event_type IN ('created','approved','rejected','modified','expired','execution_logged','reconciled','broken','cancelled')),
    from_status TEXT,
    to_status TEXT NOT NULL,
    event_payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
