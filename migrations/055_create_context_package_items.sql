CREATE TABLE IF NOT EXISTS context_package_items (
    context_package_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_package_id INTEGER NOT NULL REFERENCES context_packages(context_package_id),
    item_type TEXT NOT NULL CHECK(item_type IN (
        'reconciliation','risk_validation','order_ticket','execution','override','research_packet',
        'macro_context','senior_memo','journal','postmortem','system_health','memory'
    )),
    item_id INTEGER NOT NULL,
    item_role TEXT NOT NULL DEFAULT 'context' CHECK(item_role IN ('context','history','evidence','memory','health')),
    item_title TEXT,
    item_summary TEXT,
    validation_status TEXT NOT NULL DEFAULT 'not_checked' CHECK(validation_status IN ('not_checked','valid','invalid','warning')),
    validation_note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(context_package_id, item_type, item_id)
);
