CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL,
    institution_name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(account_type IN ('securities','cash','savings','loan','tax','other')),
    base_currency TEXT NOT NULL CHECK(length(base_currency) = 3),
    account_number_masked TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    opened_date TEXT,
    closed_date TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(account_name, institution_name)
);
