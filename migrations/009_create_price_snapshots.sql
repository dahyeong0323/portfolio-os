CREATE TABLE IF NOT EXISTS price_snapshots (
    price_snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    price_date TEXT NOT NULL,
    price_timestamp TEXT,
    currency TEXT NOT NULL CHECK(length(currency) = 3),
    price DECIMAL_TEXT NOT NULL CHECK(typeof(price) = 'text'),
    source TEXT NOT NULL CHECK(source IN ('manual','csv_import','system_correction')),
    source_ref TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(instrument_id, price_date, source, source_ref)
);
