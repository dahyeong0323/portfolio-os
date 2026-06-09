CREATE TABLE IF NOT EXISTS template_versions (
    template_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES template_registry(template_id),
    version TEXT NOT NULL,
    template_status TEXT NOT NULL DEFAULT 'draft' CHECK(template_status IN ('draft','active','retired')),
    template_body TEXT NOT NULL,
    template_hash TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0,1)),
    requires_canary INTEGER NOT NULL DEFAULT 1 CHECK(requires_canary IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    activated_at TEXT,
    retired_at TEXT,
    UNIQUE(template_id, version),
    UNIQUE(template_id, template_hash)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_template_versions_one_active
ON template_versions(template_id, template_status)
WHERE template_status = 'active';
