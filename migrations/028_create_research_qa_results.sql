CREATE TABLE IF NOT EXISTS research_qa_results (
    research_qa_id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_packet_id INTEGER NOT NULL REFERENCES research_packets(research_packet_id),
    qa_status TEXT NOT NULL CHECK(qa_status IN ('passed','failed')),
    bull_fact_count INTEGER NOT NULL DEFAULT 0,
    bear_fact_count INTEGER NOT NULL DEFAULT 0,
    neutral_fact_count INTEGER NOT NULL DEFAULT 0,
    supporting_fact_count INTEGER NOT NULL DEFAULT 0,
    challenging_fact_count INTEGER NOT NULL DEFAULT 0,
    missing_data_count INTEGER NOT NULL DEFAULT 0,
    source_count INTEGER NOT NULL DEFAULT 0,
    forbidden_language_count INTEGER NOT NULL DEFAULT 0,
    failure_reasons_json TEXT NOT NULL DEFAULT '[]',
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
