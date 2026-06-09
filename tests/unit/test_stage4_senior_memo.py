from __future__ import annotations

from datetime import date

import pytest

from portfolio_os.macro import MacroContextService
from portfolio_os.research import ResearchPacketService, ResearchQAService, ResearchSourceRepository
from portfolio_os.senior import REQUIRED_SECTION_TYPES, SeniorMemoInputBundleBuilder, SeniorMemoLintService, SeniorMemoQAService, SeniorMemoService, classify_candidate_action
from tests.conftest import seed_instrument


def create_valid_research_packet(db, symbol: str = "S4UT") -> int:
    instrument_id = seed_instrument(db, symbol)
    source = ResearchSourceRepository(db).create_source("manual_note", "Manual source", local_path=f"notes/{symbol}.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 3, 1), "Facts were collected from listed sources.", "v1")
    service = ResearchPacketService(db)
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bear", "challenging", "competition", "Competition increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "neutral", "neutral", "business", "The company reported results.")
    service.add_missing_data(packet.research_packet_id, "Retention data is unknown.", "medium", (), None)
    ResearchQAService(db).run_and_apply(packet.research_packet_id)
    return packet.research_packet_id


def create_valid_macro_context(db) -> int:
    packet = MacroContextService(db).create_macro_context_packet(date(2026, 3, 1), None, None, "Macro context was reviewed.")
    return MacroContextService(db).validate_macro_context_packet(packet.macro_context_packet_id).macro_context_packet_id


def fill_valid_memo(db, memo_id: int) -> None:
    service = SeniorMemoService(db)
    for section_type in REQUIRED_SECTION_TYPES:
        service.add_section(memo_id, section_type, section_type.replace("_", " ").title(), f"{section_type} reviewed as human memo context.")
    service.add_no_action_alternative(memo_id, "Do nothing until the next review.", "No-action keeps optionality while inputs are reviewed.")
    service.add_opposing_argument(memo_id, "The strongest opposing view is that the thesis may be incomplete.", "medium")
    service.add_decision_change_trigger(memo_id, "Ledger status or research facts change.", "ledger")


def test_senior_lint_detects_forbidden_language_but_not_fixed_disclaimer() -> None:
    lint = SeniorMemoLintService()
    assert lint.find_forbidden_execution_language("We should execute this order now.")
    assert lint.find_forbidden_execution_language("This memo is not an order ticket.") == ()


def test_portfolio_only_bundle_persists_flag_and_empty_research_is_rejected_without_it(db) -> None:
    with pytest.raises(ValueError):
        SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), ())
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (), portfolio_only=True)
    assert bundle.portfolio_only is True
    assert bundle.research_packet_ids == ()


def test_input_bundle_rejects_invalid_research_and_macro_inputs(db) -> None:
    instrument_id = seed_instrument(db, "BADR")
    invalid_packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 3, 1), "Draft packet.", "v1")
    with pytest.raises(ValueError):
        SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (invalid_packet.research_packet_id,))
    invalid_macro = MacroContextService(db).create_macro_context_packet(date(2026, 3, 1), None, None, "Draft macro context.")
    valid_research = create_valid_research_packet(db, "GOODR")
    with pytest.raises(ValueError):
        SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (valid_research,), invalid_macro.macro_context_packet_id)


def test_candidate_action_class_mapping_and_non_reconciled_block(db) -> None:
    assert classify_candidate_action("create_intent_candidate") == "risk_increasing"
    assert classify_candidate_action("reduce_risk_candidate") == "risk_reducing"
    assert classify_candidate_action("correction_review") == "correction"
    assert classify_candidate_action("research_needed") == "review_only"

    packet_id = create_valid_research_packet(db, "CAND")
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (packet_id,))
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Candidate memo", "asset", "Executive summary reviewed.")
    candidate = SeniorMemoService(db).add_candidate(memo.senior_memo_id, None, "create_intent_candidate", "Candidate action for later Stage 2 flow.", "Only a candidate.")
    assert candidate.candidate_action_class == "risk_increasing"
    assert candidate.candidate_status == "blocked_pending_reconciliation"
    assert candidate.required_next_step == "reconciliation_required"
    assert candidate.risk_validation_required is True
    assert candidate.reconciliation_required_first is True


def test_senior_memo_qa_failures_and_valid_pass(db) -> None:
    packet_id = create_valid_research_packet(db, "QAP")
    macro_id = create_valid_macro_context(db)
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (packet_id,), macro_id)
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "QA memo", "asset", "Executive summary reviewed.")
    failed = SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)
    assert failed.qa_status == "failed"
    assert failed.missing_required_sections

    fill_valid_memo(db, memo.senior_memo_id)
    passed = SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)
    assert passed.qa_status == "passed"


def test_senior_memo_qa_fails_forbidden_execution_language(db) -> None:
    packet_id = create_valid_research_packet(db, "FORB")
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 3, 1), (packet_id,))
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Bad memo", "asset", "This memo says skip risk validation.")
    fill_valid_memo(db, memo.senior_memo_id)
    result = SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)
    assert result.qa_status == "failed"
    assert result.forbidden_language_count >= 1
