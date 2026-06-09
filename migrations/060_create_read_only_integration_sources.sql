CREATE TABLE IF NOT EXISTS read_only_integration_sources (
    integration_source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK(source_type IN ('broker_export','bank_export','research_export','manual_file','other')),
    read_only_confirmed INTEGER NOT NULL CHECK(read_only_confirmed = 1),
    authority_boundary_note TEXT NOT NULL,
    connection_descriptor_json TEXT NOT NULL DEFAULT '{}',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
