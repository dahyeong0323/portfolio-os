CREATE TABLE IF NOT EXISTS research_packets (
    research_packet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    thesis_id INTEGER REFERENCES asset_theses(thesis_id),
    packet_version TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    packet_status TEXT NOT NULL DEFAULT 'draft' CHECK(packet_status IN ('draft','valid','invalid','archived')),
    summary_text TEXT,
    missing_data_summary TEXT,
    qa_status TEXT NOT NULL DEFAULT 'not_run' CHECK(qa_status IN ('not_run','passed','failed')),
    created_by TEXT NOT NULL DEFAULT 'human' CHECK(created_by IN ('human','import','system')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(instrument_id, packet_version)
);
