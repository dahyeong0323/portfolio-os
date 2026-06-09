from __future__ import annotations

from datetime import date

from portfolio_os.senior import REQUIRED_SECTION_TYPES, SeniorMemoInputBundleBuilder, SeniorMemoQAService, SeniorMemoService
from portfolio_os.senior.report_writer import SeniorMemoReportWriter
from tests.unit.test_stage4_senior_memo import create_valid_macro_context, create_valid_research_packet


def test_valid_senior_memo_flow_generates_report(db, tmp_path) -> None:
    research_id = create_valid_research_packet(db, "S4INT")
    macro_id = create_valid_macro_context(db)
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (research_id,), macro_id)
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Senior memo", "asset", "Executive summary reviewed.")
    for section_type in REQUIRED_SECTION_TYPES:
        SeniorMemoService(db).add_section(memo.senior_memo_id, section_type, section_type, f"{section_type} section text.")
    SeniorMemoService(db).add_candidate(memo.senior_memo_id, None, "review", "Review the packet again.", "Human review only.")
    SeniorMemoService(db).add_no_action_alternative(memo.senior_memo_id, "No action.", "No-action is acceptable while facts are reviewed.")
    SeniorMemoService(db).add_opposing_argument(memo.senior_memo_id, "The strongest opposing view is uncertainty.", "high")
    SeniorMemoService(db).add_decision_change_trigger(memo.senior_memo_id, "New research changes the thesis.", "research_missing_data")
    qa = SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)
    assert qa.qa_status == "passed"
    writer = SeniorMemoReportWriter(db)
    md = writer.write_markdown_report(memo.senior_memo_id, tmp_path / "senior_memo.md")
    js = writer.write_json_report(memo.senior_memo_id, tmp_path / "senior_memo.json")
    text = md.read_text(encoding="utf-8")
    assert "This memo is not an order ticket." in text
    assert "Stage 2 risk validation still required" in text
    assert md.exists()
    assert js.exists()


def test_non_reconciled_ledger_candidate_is_blocked(db) -> None:
    research_id = create_valid_research_packet(db, "S4BLK")
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (research_id,))
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Blocked memo", "asset", "Executive summary reviewed.")
    candidate = SeniorMemoService(db).add_candidate(memo.senior_memo_id, None, "create_intent_candidate", "Candidate for later upstream flow.", "Not executable here.")
    assert candidate.candidate_status == "blocked_pending_reconciliation"
    assert candidate.required_next_step == "reconciliation_required"
