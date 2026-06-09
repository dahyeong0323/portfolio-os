CREATE TABLE IF NOT EXISTS liabilities (
    liability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(account_id),
    liability_name TEXT NOT NULL,
    liability_type TEXT NOT NULL CHECK(liability_type IN ('loan','margin','credit_card','tax_payable','other')),
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    principal_amount DECIMAL_TEXT CHECK(principal_amount IS NULL OR typeof(principal_amount) = 'text'),
    current_amount DECIMAL_TEXT NOT NULL CHECK(typeof(current_amount) = 'text'),
    interest_rate_annual DECIMAL_TEXT CHECK(interest_rate_annual IS NULL OR typeof(interest_rate_annual) = 'text'),
    as_of_date TEXT NOT NULL,
    due_date TEXT,
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','csv_import','external_snapshot','system_correction')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(account_id, liability_name, liability_type, currency, as_of_date)
);
