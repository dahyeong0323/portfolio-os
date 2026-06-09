CREATE TABLE IF NOT EXISTS governance_policies (
    governance_policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL,
    version TEXT NOT NULL,
    policy_status TEXT NOT NULL DEFAULT 'draft' CHECK(policy_status IN ('draft','active','retired')),
    description TEXT,
    canary_required_before_activation INTEGER NOT NULL DEFAULT 1 CHECK(canary_required_before_activation IN (0,1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    activated_at TEXT,
    retired_at TEXT,
    UNIQUE(policy_name, version)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_policies_one_active
ON governance_policies(policy_status)
WHERE policy_status = 'active';
