CREATE TABLE IF NOT EXISTS governance_policy_rules (
    governance_rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    governance_policy_id INTEGER NOT NULL REFERENCES governance_policies(governance_policy_id),
    rule_code TEXT NOT NULL,
    rule_scope TEXT NOT NULL DEFAULT 'system' CHECK(rule_scope IN ('system','research','macro','senior_memo','context','template','integration','health')),
    rule_value TEXT NOT NULL,
    threshold_value TEXT,
    severity TEXT NOT NULL DEFAULT 'hard_block' CHECK(severity IN ('info','warning','hard_block')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(governance_policy_id, rule_code)
);
