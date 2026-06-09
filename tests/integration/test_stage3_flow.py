from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio_os.macro import MacroContextService, MacroMetricService, PortfolioContextBuilder
from portfolio_os.macro.report_writer import MacroContextReportWriter
from portfolio_os.research import ResearchPacketService, ResearchQAService, ResearchSourceRepository
from portfolio_os.research.report_writer import ResearchReportWriter
from tests.conftest import seed_account, seed_cash_anchor, seed_instrument


def _create_valid_research_packet(db, instrument_id: int) -> int:
    source = ResearchSourceRepository(db).create_source("manual_note", "Manual source", local_path="notes/source.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 2, 1), "Facts were collected from listed sources.", "v1")
    service = ResearchPacketService(db)
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bear", "challenging", "competition", "Competition increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "neutral", "neutral", "business", "The company reported quarterly results.")
    service.add_missing_data(packet.research_packet_id, "Retention data is unavailable.", "medium", ("manual search",), None)
    ResearchQAService(db).run_and_apply(packet.research_packet_id)
    return packet.research_packet_id


def test_valid_research_packet_flow_generates_reports(db, tmp_path) -> None:
    instrument_id = seed_instrument(db, "META")
    packet_id = _create_valid_research_packet(db, instrument_id)
    writer = ResearchReportWriter(db)
    md = writer.write_markdown_report(packet_id, tmp_path / "research_packet.md")
    js = writer.write_json_report(packet_id, tmp_path / "research_packet.json")
    assert md.exists()
    assert js.exists()
    assert "Research Packet" in md.read_text(encoding="utf-8")


def test_forbidden_language_packet_becomes_invalid(db) -> None:
    instrument_id = seed_instrument(db, "TSLA")
    source = ResearchSourceRepository(db).create_source("manual_note", "Manual source", local_path="notes/source.md")
    packet = ResearchPacketService(db).create_research_packet(instrument_id, None, date(2026, 2, 1), "This packet says sell.", "v1")
    service = ResearchPacketService(db)
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bull", "supporting", "financial", "Revenue increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "bear", "challenging", "competition", "Competition increased.")
    service.add_fact_with_source(packet.research_packet_id, source.source_id, "neutral", "neutral", "business", "The company reported results.")
    service.add_missing_data(packet.research_packet_id, "Retention is unknown.", "medium", (), None)
    result = ResearchQAService(db).run_and_apply(packet.research_packet_id)
    assert result.qa_status == "failed"


def test_portfolio_context_macro_flow_generates_reports(db, tmp_path) -> None:
    account_id = seed_account(db)
    seed_cash_anchor(db, account_id)
    seed_instrument(db, "AMD")
    context = PortfolioContextBuilder(db).build_context_snapshot(date(2026, 2, 1))
    metric = MacroMetricService(db).record_metric(date(2026, 2, 1), "NASDAQ_DRAWDOWN", Decimal("-0.20"), "ratio")
    corr = MacroMetricService(db).record_correlation(date(2026, 2, 1), "PORTFOLIO", "QQQ", "correlation", 30, Decimal("0.90"))
    regime = MacroMetricService(db).classify_and_record_regime(date(2026, 2, 1))
    packet = MacroContextService(db).create_macro_context_packet(
        date(2026, 2, 1),
        context.portfolio_context_id,
        regime.macro_regime_id,
        "Macro indicators were elevated and are recorded as context only.",
        risk_on_exposure="high",
        correlation_stress="elevated",
        metric_refs=(metric.macro_metric_id,),
        correlation_refs=(corr.correlation_id,),
        unknowns=("liquidity_sensitivity",),
    )
    validated = MacroContextService(db).validate_macro_context_packet(packet.macro_context_packet_id)
    assert validated.packet_status == "valid"
    writer = MacroContextReportWriter(db)
    md = writer.write_markdown_report(packet.macro_context_packet_id, tmp_path / "macro_context.md")
    js = writer.write_json_report(packet.macro_context_packet_id, tmp_path / "macro_context.json")
    assert md.exists()
    assert js.exists()
    assert "not an order ticket" in md.read_text(encoding="utf-8")
