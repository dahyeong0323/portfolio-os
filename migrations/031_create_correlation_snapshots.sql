CREATE TABLE IF NOT EXISTS correlation_snapshots (
    correlation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    left_symbol TEXT NOT NULL,
    right_symbol TEXT NOT NULL,
    metric_type TEXT NOT NULL CHECK(metric_type IN ('correlation','beta')),
    window_days INTEGER NOT NULL CHECK(window_days > 0),
    value DECIMAL_TEXT NOT NULL CHECK(typeof(value) = 'text'),
    source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','csv_import','system_calculated')),
    source_id INTEGER REFERENCES research_sources(source_id),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
