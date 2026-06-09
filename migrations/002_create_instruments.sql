CREATE TABLE IF NOT EXISTS instruments (
    instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    instrument_name TEXT NOT NULL,
    instrument_type TEXT NOT NULL CHECK(instrument_type IN ('stock','etf','crypto','fund','bond','cash_equivalent','other')),
    exchange TEXT,
    isin TEXT,
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    country TEXT,
    is_fractional_allowed INTEGER NOT NULL DEFAULT 0 CHECK(is_fractional_allowed IN (0,1)),
    quantity_precision INTEGER NOT NULL DEFAULT 6,
    price_precision INTEGER NOT NULL DEFAULT 6,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(symbol, exchange, currency)
);
