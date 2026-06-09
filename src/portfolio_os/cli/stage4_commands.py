from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from portfolio_os.db import Database
from portfolio_os.senior import SeniorMemoInputBundleBuilder, SeniorMemoInputBundleRepository, SeniorMemoQAService, SeniorMemoRepository, SeniorMemoService
from portfolio_os.senior.report_writer import SeniorMemoReportWriter
from portfolio_os.serialization import dumps_json

SENIOR_MEMO_REPORT_DIR = Path("data/exports/senior_memos")


def register_stage4_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("build-senior-input-bundle")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--research-packet-id", type=int, action="append", default=[])
    p.add_argument("--macro-context-packet-id", type=int)
    p.add_argument("--portfolio-only", action="store_true")
    p.add_argument("--no-risk-context", action="store_true")
    p.set_defaults(func=cmd_build_senior_input_bundle)

    p = subparsers.add_parser("show-senior-input-bundle")
    p.add_argument("--input-bundle-id", type=int, required=True)
    p.set_defaults(func=cmd_show_senior_input_bundle)

    p = subparsers.add_parser("create-senior-memo")
    p.add_argument("--input-bundle-id", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--scope", required=True, choices=["portfolio", "asset", "multi_asset"])
    p.add_argument("--executive-summary", required=True)
    p.add_argument("--confidence-level", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--primary-risk-summary")
    p.add_argument("--created-by", default="human")
    p.set_defaults(func=cmd_create_senior_memo)

    p = subparsers.add_parser("add-senior-section")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--section-type", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--source-ref", action="append", default=[])
    p.set_defaults(func=cmd_add_senior_section)

    p = subparsers.add_parser("add-decision-candidate")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--instrument-id", type=int)
    p.add_argument("--candidate-type", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--rationale", required=True)
    p.add_argument("--required-next-step")
    p.add_argument("--priority", default="medium", choices=["low", "medium", "high"])
    p.set_defaults(func=cmd_add_decision_candidate)

    p = subparsers.add_parser("add-no-action-alternative")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--why-reasonable", required=True)
    p.add_argument("--opportunity-cost")
    p.add_argument("--risk-reduction-benefit")
    p.add_argument("--review-trigger")
    p.set_defaults(func=cmd_add_no_action_alternative)

    p = subparsers.add_parser("add-opposing-argument")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--source-ref", action="append", default=[])
    p.set_defaults(func=cmd_add_opposing_argument)

    p = subparsers.add_parser("add-decision-change-trigger")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--type", required=True, choices=["price", "fundamental", "macro", "risk", "ledger", "tax", "execution", "research_missing_data", "other"])
    p.add_argument("--monitoring-note")
    p.set_defaults(func=cmd_add_decision_change_trigger)

    p = subparsers.add_parser("run-senior-memo-qa")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.set_defaults(func=cmd_run_senior_memo_qa)

    p = subparsers.add_parser("show-senior-memo")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.set_defaults(func=cmd_show_senior_memo)

    p = subparsers.add_parser("export-senior-memo-report")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=SENIOR_MEMO_REPORT_DIR)
    p.set_defaults(func=cmd_export_senior_memo_report)

    p = subparsers.add_parser("archive-senior-memo")
    p.add_argument("--senior-memo-id", type=int, required=True)
    p.set_defaults(func=cmd_archive_senior_memo)


def cmd_build_senior_input_bundle(args):
    with Database(args.db) as db:
        bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date.fromisoformat(args.as_of_date), tuple(args.research_packet_id), args.macro_context_packet_id, args.portfolio_only, not args.no_risk_context)
        print(dumps_json(bundle))
    return 0


def cmd_show_senior_input_bundle(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoInputBundleRepository(db).get(args.input_bundle_id)))
    return 0


def cmd_create_senior_memo(args):
    with Database(args.db) as db:
        memo = SeniorMemoService(db).create_memo(args.input_bundle_id, args.title, args.scope, args.executive_summary, args.confidence_level, args.primary_risk_summary, args.created_by)
        print(dumps_json(memo))
    return 0


def cmd_add_senior_section(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).add_section(args.senior_memo_id, args.section_type, args.title, args.text, args.source_ref)))
    return 0


def cmd_add_decision_candidate(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).add_candidate(args.senior_memo_id, args.instrument_id, args.candidate_type, args.text, args.rationale, args.required_next_step, args.priority)))
    return 0


def cmd_add_no_action_alternative(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).add_no_action_alternative(args.senior_memo_id, args.text, args.why_reasonable, args.opportunity_cost, args.risk_reduction_benefit, args.review_trigger)))
    return 0


def cmd_add_opposing_argument(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).add_opposing_argument(args.senior_memo_id, args.text, args.severity, args.source_ref)))
    return 0


def cmd_add_decision_change_trigger(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).add_decision_change_trigger(args.senior_memo_id, args.text, args.type, args.monitoring_note)))
    return 0


def cmd_run_senior_memo_qa(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoQAService(db).run_and_apply(args.senior_memo_id)))
    return 0


def cmd_show_senior_memo(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoRepository(db).get(args.senior_memo_id)))
    return 0


def cmd_export_senior_memo_report(args):
    with Database(args.db) as db:
        writer = SeniorMemoReportWriter(db)
        md_path = args.report_dir / f"senior_memo_{args.senior_memo_id}.md"
        json_path = args.report_dir / f"senior_memo_{args.senior_memo_id}.json"
        writer.write_markdown_report(args.senior_memo_id, md_path)
        writer.write_json_report(args.senior_memo_id, json_path)
        print(dumps_json({"markdown": md_path, "json": json_path}))
    return 0


def cmd_archive_senior_memo(args):
    with Database(args.db) as db:
        print(dumps_json(SeniorMemoService(db).archive_memo(args.senior_memo_id)))
    return 0
