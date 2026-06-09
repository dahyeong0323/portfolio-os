from __future__ import annotations

from datetime import date

from portfolio_os.research import ResearchLintService, ResearchPacketService, ResearchQAService, ResearchSourceRepository
from tests.conftest import seed_instrument


def _valid_packet(db) -> int:
    instrument_id = seed_instrument(db, "MSFT")
    source = ResearchSourceRepository(db).create_source("manual_note", "Buy recommendation source title is not linted", local_path="notes/msft.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 2, 1), "Revenue and margin facts were reviewed.", "v1")
    service = ResearchPacketService(db)
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased compared with the prior period.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bear", "challenging", "competition", "Competition increased in the same segment.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "neutral", "neutral", "business", "The company reported quarterly results.")
    service.add_missing_data(packet.research_packet_id, "Customer retention data was not available.", "medium", ("manual search",), "Retention would improve fact coverage.")
    return packet.research_packet_id


def test_forbidden_language_lint_detects_recommendation_terms() -> None:
    lint = ResearchLintService()
    assert lint.find_forbidden_language("The packet says investors should buy this asset.")
    assert lint.find_forbidden_language("이 문장은 매수 추천을 포함한다.")
    assert lint.find_forbidden_language("Revenue increased while margins decreased.") == ()


def test_valid_packet_passes_strict_stage3_qa_and_ignores_source_title(db) -> None:
    packet_id = _valid_packet(db)
    result = ResearchQAService(db).run_and_apply(packet_id)
    assert result.qa_status == "passed"
    assert result.bull_fact_count == 1
    assert result.bear_fact_count == 1
    assert result.neutral_fact_count == 1
    assert result.supporting_fact_count == 1
    assert result.challenging_fact_count == 1
    assert result.missing_data_count == 1
    assert result.source_count == 1
    assert result.forbidden_language_count == 0


def test_research_qa_fails_without_required_antithesis_and_missing_data(db) -> None:
    instrument_id = seed_instrument(db, "GOOG")
    source = ResearchSourceRepository(db).create_source("manual_note", "Source", local_path="notes/goog.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 2, 1), "Only one side of the case was entered.", "v1")
    ResearchPacketService(db).add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased.")
    result = ResearchQAService(db).run_and_apply(packet.research_packet_id)
    assert result.qa_status == "failed"
    assert any("bear fact" in reason for reason in result.failure_reasons)
    assert any("thesis-challenging" in reason for reason in result.failure_reasons)
    assert any("missing data" in reason for reason in result.failure_reasons)


def test_research_qa_fails_on_summary_and_fact_forbidden_language_only(db) -> None:
    instrument_id = seed_instrument(db, "NVDA")
    source = ResearchSourceRepository(db).create_source("manual_note", "Source", local_path="notes/nvda.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 2, 1), "This summary says should buy.", "v1")
    service = ResearchPacketService(db)
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bear", "challenging", "competition", "Competition increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "neutral", "neutral", "business", "The company reported results.")
    service.add_missing_data(packet.research_packet_id, "Retention is unknown.", "medium", (), None)
    result = ResearchQAService(db).run_and_apply(packet.research_packet_id)
    assert result.qa_status == "failed"
    assert result.forbidden_language_count >= 1
