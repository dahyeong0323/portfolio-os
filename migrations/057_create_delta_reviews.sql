CREATE TABLE IF NOT EXISTS delta_reviews (
    delta_review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_name TEXT NOT NULL,
    previous_context_package_id INTEGER REFERENCES context_packages(context_package_id),
    current_context_package_id INTEGER REFERENCES context_packages(context_package_id),
    review_status TEXT NOT NULL DEFAULT 'draft' CHECK(review_status IN ('draft','complete','archived')),
    added_items_json TEXT NOT NULL DEFAULT '[]',
    removed_items_json TEXT NOT NULL DEFAULT '[]',
    changed_items_json TEXT NOT NULL DEFAULT '[]',
    review_summary TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
