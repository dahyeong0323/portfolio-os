CREATE TABLE IF NOT EXISTS fx_rates (
    fx_rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rate_date TEXT NOT NULL,
    base_currency TEXT NOT NULL CHECK(length(base_currency) = 3),
    quote_currency TEXT NOT NULL CHECK(length(quote_currency) = 3),
    rate DECIMAL_TEXT NOT NULL CHECK(typeof(rate) = 'text'),
    source TEXT NOT NULL CHECK(source IN ('manual','csv_import','system_correction')),
    source_ref TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(rate_date, base_currency, quote_currency, source, source_ref)
);
