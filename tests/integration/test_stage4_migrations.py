from __future__ import annotations


def test_stage4_migrations_apply_after_stage1_stage2_stage3(db) -> None:
    tables = {
        row["name"]
        for row in db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('senior_memo_input_bundles','senior_memos','senior_memo_sections','decision_candidates','senior_memo_qa_results')"
        )
    }
    assert tables == {"senior_memo_input_bundles", "senior_memos", "senior_memo_sections", "decision_candidates", "senior_memo_qa_results"}
    versions = [row["version"] for row in db.fetch_all("SELECT version FROM schema_migrations ORDER BY version")]
    assert 44 in versions
