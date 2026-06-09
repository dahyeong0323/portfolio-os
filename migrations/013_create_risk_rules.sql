CREATE TABLE IF NOT EXISTS risk_rules (
    risk_rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_version_id INTEGER NOT NULL REFERENCES risk_policy_versions(policy_version_id),
    rule_code TEXT NOT NULL,
    rule_scope TEXT NOT NULL CHECK(rule_scope IN ('global','account','instrument','bucket')),
    account_id INTEGER REFERENCES accounts(account_id),
    instrument_id INTEGER REFERENCES instruments(instrument_id),
    risk_bucket TEXT,
    threshold_value DECIMAL_TEXT NOT NULL CHECK(typeof(threshold_value) = 'text'),
    threshold_unit TEXT NOT NULL CHECK(threshold_unit IN ('amount','ratio','count')),
    currency TEXT CHECK(currency IS NULL OR length(currency) = 3),
    severity TEXT NOT NULL CHECK(severity IN ('hard_block','adjust_down','warn')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
