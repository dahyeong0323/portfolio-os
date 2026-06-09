CREATE TABLE IF NOT EXISTS asset_theses (
    thesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    thesis_title TEXT NOT NULL,
    thesis_text TEXT NOT NULL,
    invalidation_triggers_json TEXT NOT NULL DEFAULT '[]',
    watch_questions_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','paused','invalidated','archived')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
