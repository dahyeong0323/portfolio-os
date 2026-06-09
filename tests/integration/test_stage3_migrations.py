from __future__ import annotations


def test_stage3_migrations_apply_after_stage1_and_stage2(db) -> None:
    tables = {
        row["name"]
        for row in db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('asset_theses','research_sources','research_packets','macro_context_packets')"
        )
    }
    assert tables == {"asset_theses", "research_sources", "research_packets", "macro_context_packets"}
    latest = db.fetch_one("SELECT MAX(version) AS version FROM schema_migrations")
    versions = [row["version"] for row in db.fetch_all("SELECT version FROM schema_migrations ORDER BY version")]
    assert 35 in versions
    assert latest["version"] >= 35
