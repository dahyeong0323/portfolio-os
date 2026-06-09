CREATE TABLE IF NOT EXISTS context_budget_records (
    context_budget_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_package_id INTEGER NOT NULL REFERENCES context_packages(context_package_id),
    item_count INTEGER NOT NULL CHECK(item_count >= 0),
    max_item_count INTEGER NOT NULL CHECK(max_item_count >= 0),
    warning_item_count INTEGER NOT NULL CHECK(warning_item_count >= 0),
    estimated_token_count INTEGER NOT NULL DEFAULT 0 CHECK(estimated_token_count >= 0),
    budget_status TEXT NOT NULL CHECK(budget_status IN ('ok','warning','failed')),
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
