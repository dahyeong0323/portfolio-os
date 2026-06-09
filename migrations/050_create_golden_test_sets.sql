CREATE TABLE IF NOT EXISTS golden_test_sets (
    golden_test_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
    set_name TEXT NOT NULL,
    set_version TEXT NOT NULL,
    test_scope TEXT NOT NULL DEFAULT 'authority_boundary' CHECK(test_scope IN ('authority_boundary','template','context','integration','system')),
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(set_name, set_version)
);
