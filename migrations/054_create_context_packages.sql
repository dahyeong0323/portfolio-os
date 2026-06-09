CREATE TABLE IF NOT EXISTS context_packages (
    context_package_id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name TEXT NOT NULL,
    package_scope TEXT NOT NULL DEFAULT 'review' CHECK(package_scope IN ('review','portfolio_review','memo_support','audit','health')),
    as_of_date TEXT NOT NULL,
    package_status TEXT NOT NULL DEFAULT 'draft' CHECK(package_status IN ('draft','valid','invalid','archived')),
    ledger_status TEXT,
    latest_reconciliation_id INTEGER,
    summary_text TEXT,
    budget_status TEXT NOT NULL DEFAULT 'not_checked' CHECK(budget_status IN ('not_checked','ok','warning','failed')),
    created_by TEXT NOT NULL DEFAULT 'human' CHECK(created_by IN ('human','system','import')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
