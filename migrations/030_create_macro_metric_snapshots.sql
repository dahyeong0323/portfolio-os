CREATE TABLE IF NOT EXISTS macro_metric_snapshots (
    macro_metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_date TEXT NOT NULL,
    metric_code TEXT NOT NULL,
    metric_value DECIMAL_TEXT NOT NULL CHECK(typeof(metric_value) = 'text'),
    metric_unit TEXT NOT NULL CHECK(metric_unit IN ('ratio','percent','index','amount')),
    source_id INTEGER REFERENCES research_sources(source_id),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
