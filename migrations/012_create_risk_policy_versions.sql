CREATE TABLE IF NOT EXISTS risk_policy_versions (
    policy_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    version TEXT NOT NULL,
    base_currency TEXT NOT NULL CHECK(length(base_currency) = 3),
    is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0,1)),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(policy_name, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_one_active_risk_policy
ON risk_policy_versions(is_active)
WHERE is_active = 1;
