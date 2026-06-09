CREATE TABLE IF NOT EXISTS read_only_import_runs (
    import_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    integration_source_id INTEGER NOT NULL REFERENCES read_only_integration_sources(integration_source_id),
    import_scope TEXT NOT NULL CHECK(import_scope IN ('snapshot','research','statement','audit','other')),
    import_status TEXT NOT NULL CHECK(import_status IN ('recorded','passed','failed')),
    artifact_path TEXT,
    rows_seen INTEGER NOT NULL DEFAULT 0 CHECK(rows_seen >= 0),
    rows_imported INTEGER NOT NULL DEFAULT 0 CHECK(rows_imported >= 0),
    checksum TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
