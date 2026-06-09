CREATE TABLE IF NOT EXISTS research_missing_data (
    missing_data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_packet_id INTEGER NOT NULL REFERENCES research_packets(research_packet_id),
    data_question TEXT NOT NULL,
    importance TEXT NOT NULL DEFAULT 'medium' CHECK(importance IN ('low','medium','high','critical')),
    attempted_sources_json TEXT NOT NULL DEFAULT '[]',
    impact_note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
