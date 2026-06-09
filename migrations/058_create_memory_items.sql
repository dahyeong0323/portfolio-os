CREATE TABLE IF NOT EXISTS memory_items (
    memory_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('operating_rule','known_limitation','decision_rationale','user_preference','system_note')),
    memory_key TEXT NOT NULL UNIQUE,
    memory_text TEXT NOT NULL,
    source_item_type TEXT,
    source_item_id INTEGER,
    importance TEXT NOT NULL DEFAULT 'medium' CHECK(importance IN ('low','medium','high','critical')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
