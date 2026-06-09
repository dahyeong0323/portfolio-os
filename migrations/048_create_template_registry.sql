CREATE TABLE IF NOT EXISTS template_registry (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL UNIQUE,
    template_type TEXT NOT NULL CHECK(template_type IN ('research_report','macro_report','senior_memo','context_package','governance_report','canary_report','health_report','other')),
    template_scope TEXT NOT NULL DEFAULT 'system' CHECK(template_scope IN ('system','stage3','stage4','stage5')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
