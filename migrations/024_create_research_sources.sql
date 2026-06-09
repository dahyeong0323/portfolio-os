CREATE TABLE IF NOT EXISTS research_sources (
    source_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK(source_type IN ('filing','earnings','news','price_data','company_website','analyst_note','macro_data','manual_note','other')),
    title TEXT NOT NULL,
    publisher TEXT,
    url TEXT,
    local_path TEXT,
    published_at TEXT,
    retrieved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    source_hash TEXT,
    freshness_status TEXT NOT NULL DEFAULT 'unknown' CHECK(freshness_status IN ('fresh','stale','unknown')),
    reliability_note TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK(url IS NOT NULL OR local_path IS NOT NULL)
);
