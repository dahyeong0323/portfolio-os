CREATE TABLE IF NOT EXISTS postmortem_tasks (
    postmortem_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_ticket_id INTEGER REFERENCES order_tickets(order_ticket_id),
    override_ticket_id INTEGER REFERENCES override_tickets(override_ticket_id),
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('scheduled','completed','cancelled','overdue')),
    prompt_questions_json TEXT NOT NULL DEFAULT '[]',
    completed_decision_id INTEGER REFERENCES decision_journal(decision_id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
