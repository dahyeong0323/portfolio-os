CREATE TABLE IF NOT EXISTS research_facts (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_packet_id INTEGER NOT NULL REFERENCES research_packets(research_packet_id),
    source_id INTEGER NOT NULL REFERENCES research_sources(source_id),
    fact_category TEXT NOT NULL CHECK(fact_category IN ('bull','bear','neutral')),
    thesis_relation TEXT NOT NULL CHECK(thesis_relation IN ('supporting','challenging','neutral','unknown')),
    fact_type TEXT NOT NULL CHECK(fact_type IN ('price','financial','business','product','management','dilution','competition','macro','technical','other')),
    fact_text TEXT NOT NULL,
    numeric_value DECIMAL_TEXT CHECK(numeric_value IS NULL OR typeof(numeric_value) = 'text'),
    numeric_unit TEXT,
    observed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
