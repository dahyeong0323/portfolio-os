CREATE TABLE IF NOT EXISTS cash_balances (
    cash_balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    as_of_date TEXT NOT NULL,
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    amount DECIMAL_TEXT NOT NULL CHECK(typeof(amount) = 'text'),
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','csv_import','system_correction')),
    external_ref TEXT,
    is_reconciled INTEGER NOT NULL DEFAULT 0 CHECK(is_reconciled IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(account_id, as_of_date, currency)
);
