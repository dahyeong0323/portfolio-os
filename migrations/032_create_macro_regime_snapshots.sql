CREATE TABLE IF NOT EXISTS macro_regime_snapshots (
    macro_regime_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    regime TEXT NOT NULL CHECK(regime IN ('normal','stress','crisis','unknown')),
    confidence TEXT NOT NULL DEFAULT 'medium' CHECK(confidence IN ('low','medium','high')),
    reason_summary TEXT NOT NULL,
    metric_refs_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
