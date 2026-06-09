CREATE TABLE IF NOT EXISTS decision_journal (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_type TEXT NOT NULL CHECK(decision_type IN ('ticket_approval','ticket_rejection','ticket_modification','override_declared','manual_execution_logged','postmortem')),
    order_ticket_id INTEGER REFERENCES order_tickets(order_ticket_id),
    override_ticket_id INTEGER REFERENCES override_tickets(override_ticket_id),
    risk_validation_id INTEGER REFERENCES risk_validation_results(risk_validation_id),
    manual_execution_id INTEGER REFERENCES manual_execution_logs(manual_execution_id),
    human_decision TEXT NOT NULL,
    reason TEXT,
    emotional_state TEXT,
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
