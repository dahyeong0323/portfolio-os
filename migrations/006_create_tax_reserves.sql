CREATE TABLE IF NOT EXISTS tax_reserves (
    tax_reserve_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(account_id),
    tax_year INTEGER NOT NULL CHECK(tax_year >= 2000),
    tax_type TEXT NOT NULL CHECK(tax_type IN ('capital_gains','dividend','interest','wealth','income','other')),
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    reserved_amount DECIMAL_TEXT NOT NULL CHECK(typeof(reserved_amount) = 'text'),
    as_of_date TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','csv_import','external_snapshot','system_correction')),
    calculation_basis TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(account_id, tax_year, tax_type, currency, as_of_date)
);
