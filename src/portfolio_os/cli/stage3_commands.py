from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from portfolio_os.db import Database
from portfolio_os.macro import MacroContextService, MacroMetricService, PortfolioContextBuilder
from portfolio_os.macro.report_writer import MacroContextReportWriter
from portfolio_os.macro.repositories import (
    CorrelationRepository,
    MacroContextPacketRepository,
    MacroMetricRepository,
    MacroRegimeRepository,
    PortfolioContextRepository,
)
from portfolio_os.research import AssetThesisRepository, ResearchPacketRepository, ResearchPacketService, ResearchQAService, ResearchSourceRepository
from portfolio_os.research.report_writer import ResearchReportWriter
from portfolio_os.serialization import dumps_json

RESEARCH_REPORT_DIR = Path("data/exports/research_reports")
MACRO_REPORT_DIR = Path("data/exports/macro_reports")


def register_stage3_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("create-thesis")
    p.add_argument("--instrument-id", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--invalidation-trigger", action="append", default=[])
    p.add_argument("--watch-question", action="append", default=[])
    p.set_defaults(func=cmd_create_thesis)

    p = subparsers.add_parser("update-thesis-status")
    p.add_argument("--thesis-id", type=int, required=True)
    p.add_argument("--status", required=True, choices=["active", "paused", "invalidated", "archived"])
    p.set_defaults(func=cmd_update_thesis_status)

    p = subparsers.add_parser("add-research-source")
    p.add_argument("--type", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--publisher")
    p.add_argument("--url")
    p.add_argument("--local-path")
    p.add_argument("--published-at")
    p.add_argument("--source-hash")
    p.add_argument("--freshness-status", default="unknown", choices=["fresh", "stale", "unknown"])
    p.add_argument("--reliability-note")
    p.set_defaults(func=cmd_add_research_source)

    subparsers.add_parser("list-research-sources").set_defaults(func=cmd_list_research_sources)

    p = subparsers.add_parser("create-research-packet")
    p.add_argument("--instrument-id", type=int, required=True)
    p.add_argument("--thesis-id", type=int)
    p.add_argument("--packet-version", default="v1")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--summary-text")
    p.add_argument("--missing-data-summary")
    p.add_argument("--created-by", default="human")
    p.set_defaults(func=cmd_create_research_packet)

    p = subparsers.add_parser("add-research-fact")
    p.add_argument("--research-packet-id", type=int, required=True)
    p.add_argument("--source-id", type=int, required=True)
    p.add_argument("--category", required=True, choices=["bull", "bear", "neutral"])
    p.add_argument("--thesis-relation", required=True, choices=["supporting", "challenging", "neutral", "unknown"])
    p.add_argument("--fact-type", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--numeric-value")
    p.add_argument("--numeric-unit")
    p.add_argument("--observed-at")
    p.set_defaults(func=cmd_add_research_fact)

    p = subparsers.add_parser("add-missing-data")
    p.add_argument("--research-packet-id", type=int, required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--importance", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--attempted-source", action="append", default=[])
    p.add_argument("--impact-note")
    p.set_defaults(func=cmd_add_missing_data)

    p = subparsers.add_parser("run-research-qa")
    p.add_argument("--research-packet-id", type=int, required=True)
    p.set_defaults(func=cmd_run_research_qa)

    p = subparsers.add_parser("show-research-packet")
    p.add_argument("--research-packet-id", type=int, required=True)
    p.set_defaults(func=cmd_show_research_packet)

    p = subparsers.add_parser("export-research-report")
    p.add_argument("--research-packet-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=RESEARCH_REPORT_DIR)
    p.set_defaults(func=cmd_export_research_report)

    p = subparsers.add_parser("build-portfolio-context")
    p.add_argument("--as-of-date", required=True)
    p.set_defaults(func=cmd_build_portfolio_context)

    p = subparsers.add_parser("show-portfolio-context")
    p.add_argument("--portfolio-context-id", type=int)
    p.set_defaults(func=cmd_show_portfolio_context)

    p = subparsers.add_parser("record-macro-metric")
    p.add_argument("--metric-date", required=True)
    p.add_argument("--metric-code", required=True)
    p.add_argument("--metric-value", required=True)
    p.add_argument("--metric-unit", required=True, choices=["ratio", "percent", "index", "amount"])
    p.add_argument("--source-id", type=int)
    p.add_argument("--notes")
    p.set_defaults(func=cmd_record_macro_metric)

    p = subparsers.add_parser("record-correlation")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--left-symbol", required=True)
    p.add_argument("--right-symbol", required=True)
    p.add_argument("--metric-type", required=True, choices=["correlation", "beta"])
    p.add_argument("--window-days", type=int, required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--source", default="manual", choices=["manual", "csv_import", "system_calculated"])
    p.add_argument("--source-id", type=int)
    p.add_argument("--notes")
    p.set_defaults(func=cmd_record_correlation)

    p = subparsers.add_parser("classify-macro-regime")
    p.add_argument("--as-of-date", required=True)
    p.set_defaults(func=cmd_classify_macro_regime)

    p = subparsers.add_parser("create-crash-playbook-rule")
    p.add_argument("--name", required=True)
    p.add_argument("--trigger-conditions-json", default="{}")
    p.add_argument("--context-note", required=True)
    p.add_argument("--forbidden-uses-json", default="[]")
    p.set_defaults(func=cmd_create_crash_playbook_rule)

    p = subparsers.add_parser("create-macro-context")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--portfolio-context-id", type=int)
    p.add_argument("--macro-regime-id", type=int)
    p.add_argument("--summary-text", required=True)
    p.add_argument("--risk-on-exposure", default="unknown", choices=["low", "medium", "high", "extreme", "unknown"])
    p.add_argument("--liquidity-sensitivity", default="unknown", choices=["low", "medium", "high", "unknown"])
    p.add_argument("--btc-related-exposure", default="unknown", choices=["low", "medium", "high", "unknown"])
    p.add_argument("--nasdaq-growth-exposure", default="unknown", choices=["low", "medium", "high", "unknown"])
    p.add_argument("--correlation-stress", default="unknown", choices=["normal", "elevated", "extreme", "unknown"])
    p.add_argument("--defensive-buffer", default="unknown", choices=["adequate", "thin", "missing", "unknown"])
    p.add_argument("--metric-ref", type=int, action="append", default=[])
    p.add_argument("--correlation-ref", type=int, action="append", default=[])
    p.add_argument("--crash-rule-ref", type=int, action="append", default=[])
    p.add_argument("--unknown", action="append", default=[])
    p.set_defaults(func=cmd_create_macro_context)

    p = subparsers.add_parser("validate-macro-context")
    p.add_argument("--macro-context-packet-id", type=int, required=True)
    p.set_defaults(func=cmd_validate_macro_context)

    p = subparsers.add_parser("show-macro-context")
    p.add_argument("--macro-context-packet-id", type=int, required=True)
    p.set_defaults(func=cmd_show_macro_context)

    p = subparsers.add_parser("export-macro-context-report")
    p.add_argument("--macro-context-packet-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=MACRO_REPORT_DIR)
    p.set_defaults(func=cmd_export_macro_context_report)


def _dt(text: str | None) -> datetime | None:
    return datetime.fromisoformat(text.replace("Z", "+00:00")) if text else None


def cmd_create_thesis(args):
    with Database(args.db) as db:
        print(dumps_json(AssetThesisRepository(db).create_thesis(args.instrument_id, args.title, args.text, args.invalidation_trigger, args.watch_question)))
    return 0


def cmd_update_thesis_status(args):
    with Database(args.db) as db:
        print(dumps_json(AssetThesisRepository(db).update_status(args.thesis_id, args.status)))
    return 0


def cmd_add_research_source(args):
    with Database(args.db) as db:
        print(dumps_json(ResearchSourceRepository(db).create_source(args.type, args.title, args.publisher, args.url, args.local_path, _dt(args.published_at), args.source_hash, args.freshness_status, args.reliability_note)))
    return 0


def cmd_list_research_sources(args):
    with Database(args.db) as db:
        print(dumps_json(ResearchSourceRepository(db).list_sources()))
    return 0


def cmd_create_research_packet(args):
    with Database(args.db) as db:
        packet = ResearchPacketService(db).create_research_packet(args.instrument_id, args.thesis_id, date.fromisoformat(args.as_of_date), args.summary_text, args.packet_version, args.missing_data_summary, args.created_by)
        print(dumps_json(packet))
    return 0


def cmd_add_research_fact(args):
    with Database(args.db) as db:
        fact = ResearchPacketService(db).add_fact_with_source(
            args.research_packet_id,
            args.source_id,
            args.category,
            args.thesis_relation,
            args.fact_type,
            args.text,
            Decimal(args.numeric_value) if args.numeric_value else None,
            args.numeric_unit,
            _dt(args.observed_at),
        )
        print(dumps_json(fact))
    return 0


def cmd_add_missing_data(args):
    with Database(args.db) as db:
        print(dumps_json(ResearchPacketService(db).add_missing_data(args.research_packet_id, args.question, args.importance, args.attempted_source, args.impact_note)))
    return 0


def cmd_run_research_qa(args):
    with Database(args.db) as db:
        print(dumps_json(ResearchQAService(db).run_and_apply(args.research_packet_id)))
    return 0


def cmd_show_research_packet(args):
    with Database(args.db) as db:
        packet = ResearchPacketRepository(db).get(args.research_packet_id)
        print(dumps_json(packet))
    return 0


def cmd_export_research_report(args):
    with Database(args.db) as db:
        writer = ResearchReportWriter(db)
        md_path = args.report_dir / f"research_packet_{args.research_packet_id}.md"
        json_path = args.report_dir / f"research_packet_{args.research_packet_id}.json"
        writer.write_markdown_report(args.research_packet_id, md_path)
        writer.write_json_report(args.research_packet_id, json_path)
        print(dumps_json({"markdown": md_path, "json": json_path}))
    return 0


def cmd_build_portfolio_context(args):
    with Database(args.db) as db:
        print(dumps_json(PortfolioContextBuilder(db).build_context_snapshot(date.fromisoformat(args.as_of_date))))
    return 0


def cmd_show_portfolio_context(args):
    with Database(args.db) as db:
        repo = PortfolioContextRepository(db)
        context = repo.get(args.portfolio_context_id) if args.portfolio_context_id else repo.get_latest_context()
        print(dumps_json(context))
    return 0


def cmd_record_macro_metric(args):
    with Database(args.db) as db:
        print(dumps_json(MacroMetricService(db).record_metric(date.fromisoformat(args.metric_date), args.metric_code, Decimal(args.metric_value), args.metric_unit, args.source_id, args.notes)))
    return 0


def cmd_record_correlation(args):
    with Database(args.db) as db:
        print(dumps_json(MacroMetricService(db).record_correlation(date.fromisoformat(args.as_of_date), args.left_symbol, args.right_symbol, args.metric_type, args.window_days, Decimal(args.value), args.source, args.source_id, args.notes)))
    return 0


def cmd_classify_macro_regime(args):
    with Database(args.db) as db:
        print(dumps_json(MacroMetricService(db).classify_and_record_regime(date.fromisoformat(args.as_of_date))))
    return 0


def cmd_create_crash_playbook_rule(args):
    json.loads(args.trigger_conditions_json)
    json.loads(args.forbidden_uses_json)
    with Database(args.db) as db:
        print(dumps_json(MacroContextService(db).create_crash_playbook_rule(args.name, args.trigger_conditions_json, args.context_note, args.forbidden_uses_json)))
    return 0


def cmd_create_macro_context(args):
    with Database(args.db) as db:
        packet = MacroContextService(db).create_macro_context_packet(
            date.fromisoformat(args.as_of_date),
            args.portfolio_context_id,
            args.macro_regime_id,
            args.summary_text,
            args.risk_on_exposure,
            args.liquidity_sensitivity,
            args.btc_related_exposure,
            args.nasdaq_growth_exposure,
            args.correlation_stress,
            args.defensive_buffer,
            args.metric_ref,
            args.correlation_ref,
            args.crash_rule_ref,
            args.unknown,
        )
        print(dumps_json(packet))
    return 0


def cmd_validate_macro_context(args):
    with Database(args.db) as db:
        print(dumps_json(MacroContextService(db).validate_macro_context_packet(args.macro_context_packet_id)))
    return 0


def cmd_show_macro_context(args):
    with Database(args.db) as db:
        print(dumps_json(MacroContextPacketRepository(db).get(args.macro_context_packet_id)))
    return 0


def cmd_export_macro_context_report(args):
    with Database(args.db) as db:
        writer = MacroContextReportWriter(db)
        md_path = args.report_dir / f"macro_context_{args.macro_context_packet_id}.md"
        json_path = args.report_dir / f"macro_context_{args.macro_context_packet_id}.json"
        writer.write_markdown_report(args.macro_context_packet_id, md_path)
        writer.write_json_report(args.macro_context_packet_id, json_path)
        print(dumps_json({"markdown": md_path, "json": json_path}))
    return 0
