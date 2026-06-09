from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from portfolio_os.context import ContextPackageRepository, ContextPackageService, DeltaReviewService, MemoryService
from portfolio_os.context.report_writer import ContextPackageReportWriter
from portfolio_os.db import Database
from portfolio_os.governance import (
    CanaryRepository,
    CanaryService,
    ConfigurationSnapshotService,
    GoldenTestRepository,
    GovernancePolicyRepository,
    GovernancePolicyService,
    SystemHealthRepository,
    SystemHealthService,
    TemplateGovernanceService,
    TemplateRepository,
)
from portfolio_os.governance.report_writer import CanaryReportWriter, GovernanceReportWriter, SystemHealthReportWriter
from portfolio_os.integrations import ReadOnlyIntegrationService
from portfolio_os.serialization import dumps_json

GOVERNANCE_REPORT_DIR = Path("data/exports/governance_reports")
CONTEXT_PACKAGE_REPORT_DIR = Path("data/exports/context_packages")
CANARY_REPORT_DIR = Path("data/exports/canary_reports")
HEALTH_REPORT_DIR = Path("data/exports/health_reports")


def register_stage5_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("seed-default-governance-policy")
    p.add_argument("--activate", action="store_true")
    p.add_argument("--report-dir", type=Path, default=GOVERNANCE_REPORT_DIR)
    p.set_defaults(func=cmd_seed_default_governance_policy)

    p = subparsers.add_parser("activate-governance-policy")
    p.add_argument("--governance-policy-id", type=int, required=True)
    p.set_defaults(func=cmd_activate_governance_policy)

    p = subparsers.add_parser("list-governance-rules")
    p.add_argument("--governance-policy-id", type=int)
    p.set_defaults(func=cmd_list_governance_rules)

    p = subparsers.add_parser("capture-configuration-snapshot")
    p.add_argument("--name", required=True)
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--scope", default="system")
    p.set_defaults(func=cmd_capture_configuration_snapshot)

    p = subparsers.add_parser("register-template")
    p.add_argument("--name", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--scope", default="stage5")
    p.add_argument("--description")
    p.set_defaults(func=cmd_register_template)

    p = subparsers.add_parser("create-template-version")
    p.add_argument("--template-id", type=int, required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--default", action="store_true")
    p.add_argument("--no-canary", action="store_true")
    p.set_defaults(func=cmd_create_template_version)

    p = subparsers.add_parser("activate-template-version")
    p.add_argument("--template-version-id", type=int, required=True)
    p.set_defaults(func=cmd_activate_template_version)

    p = subparsers.add_parser("create-golden-test-set")
    p.add_argument("--name", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--scope", default="authority_boundary")
    p.add_argument("--description")
    p.set_defaults(func=cmd_create_golden_test_set)

    p = subparsers.add_parser("add-golden-test-case")
    p.add_argument("--golden-test-set-id", type=int, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--input-text", required=True)
    p.add_argument("--expected-status", required=True, choices=["passed", "failed", "warning"])
    p.add_argument("--expected-reason")
    p.set_defaults(func=cmd_add_golden_test_case)

    p = subparsers.add_parser("run-canary")
    p.add_argument("--scope", default="system")
    p.add_argument("--golden-test-set-id", type=int, action="append", default=[])
    p.add_argument("--configuration-snapshot-id", type=int)
    p.set_defaults(func=cmd_run_canary)

    p = subparsers.add_parser("show-canary-run")
    p.add_argument("--canary-run-id", type=int, required=True)
    p.set_defaults(func=cmd_show_canary_run)

    p = subparsers.add_parser("export-canary-report")
    p.add_argument("--canary-run-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=CANARY_REPORT_DIR)
    p.set_defaults(func=cmd_export_canary_report)

    p = subparsers.add_parser("create-context-package")
    p.add_argument("--name", required=True)
    p.add_argument("--scope", default="review")
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--summary-text")
    p.add_argument("--created-by", default="human")
    p.set_defaults(func=cmd_create_context_package)

    p = subparsers.add_parser("add-context-item")
    p.add_argument("--context-package-id", type=int, required=True)
    p.add_argument("--item-type", required=True)
    p.add_argument("--item-id", type=int, required=True)
    p.add_argument("--role", default="context")
    p.add_argument("--title")
    p.add_argument("--summary")
    p.set_defaults(func=cmd_add_context_item)

    p = subparsers.add_parser("validate-context-package")
    p.add_argument("--context-package-id", type=int, required=True)
    p.set_defaults(func=cmd_validate_context_package)

    p = subparsers.add_parser("export-context-package")
    p.add_argument("--context-package-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=CONTEXT_PACKAGE_REPORT_DIR)
    p.set_defaults(func=cmd_export_context_package)

    p = subparsers.add_parser("create-delta-review")
    p.add_argument("--name", required=True)
    p.add_argument("--previous-context-package-id", type=int)
    p.add_argument("--current-context-package-id", type=int)
    p.add_argument("--summary")
    p.set_defaults(func=cmd_create_delta_review)

    p = subparsers.add_parser("create-memory-item")
    p.add_argument("--type", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--source-item-type")
    p.add_argument("--source-item-id", type=int)
    p.add_argument("--importance", default="medium")
    p.set_defaults(func=cmd_create_memory_item)

    p = subparsers.add_parser("list-memory-items")
    p.add_argument("--type")
    p.set_defaults(func=cmd_list_memory_items)

    p = subparsers.add_parser("capture-system-health")
    p.add_argument("--as-of-date", required=True)
    p.set_defaults(func=cmd_capture_system_health)

    p = subparsers.add_parser("export-system-health-report")
    p.add_argument("--system-health-snapshot-id", type=int, required=True)
    p.add_argument("--report-dir", type=Path, default=HEALTH_REPORT_DIR)
    p.set_defaults(func=cmd_export_system_health_report)

    p = subparsers.add_parser("register-read-only-source")
    p.add_argument("--name", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--read-only-confirmed", action="store_true")
    p.add_argument("--authority-boundary-note", required=True)
    p.add_argument("--connection-descriptor-json", default="{}")
    p.set_defaults(func=cmd_register_read_only_source)

    p = subparsers.add_parser("record-read-only-import")
    p.add_argument("--integration-source-id", type=int, required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--status", required=True, choices=["recorded", "passed", "failed"])
    p.add_argument("--artifact-path")
    p.add_argument("--rows-seen", type=int, default=0)
    p.add_argument("--rows-imported", type=int, default=0)
    p.add_argument("--checksum")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_record_read_only_import)


def cmd_seed_default_governance_policy(args):
    with Database(args.db) as db:
        policy = GovernancePolicyService(db).seed_default_policy(args.activate)
        writer = GovernanceReportWriter(db)
        md = args.report_dir / f"governance_policy_{policy.governance_policy_id}.md"
        js = args.report_dir / f"governance_policy_{policy.governance_policy_id}.json"
        writer.write_policy_report(policy.governance_policy_id, md)
        writer.write_policy_json(policy.governance_policy_id, js)
        print(dumps_json({"policy": policy, "markdown": md, "json": js}))
    return 0


def cmd_activate_governance_policy(args):
    with Database(args.db) as db:
        print(dumps_json(GovernancePolicyService(db).activate_policy(args.governance_policy_id)))
    return 0


def cmd_list_governance_rules(args):
    with Database(args.db) as db:
        print(dumps_json(GovernancePolicyRepository(db).list_rules(args.governance_policy_id)))
    return 0


def cmd_capture_configuration_snapshot(args):
    with Database(args.db) as db:
        print(dumps_json(ConfigurationSnapshotService(db).capture_snapshot(args.name, date.fromisoformat(args.as_of_date), args.scope)))
    return 0


def cmd_register_template(args):
    with Database(args.db) as db:
        print(dumps_json(TemplateGovernanceService(db).register_template(args.name, args.type, args.scope, args.description)))
    return 0


def cmd_create_template_version(args):
    with Database(args.db) as db:
        requires_canary = False if args.no_canary else None
        print(dumps_json(TemplateGovernanceService(db).create_template_version(args.template_id, args.version, args.body, args.default, requires_canary)))
    return 0


def cmd_activate_template_version(args):
    with Database(args.db) as db:
        print(dumps_json(TemplateGovernanceService(db).activate_template_version(args.template_version_id)))
    return 0


def cmd_create_golden_test_set(args):
    with Database(args.db) as db:
        print(dumps_json(GoldenTestRepository(db).create_set(args.name, args.version, args.scope, args.description)))
    return 0


def cmd_add_golden_test_case(args):
    with Database(args.db) as db:
        print(dumps_json(GoldenTestRepository(db).add_case(args.golden_test_set_id, args.name, args.type, args.input_text, args.expected_status, args.expected_reason)))
    return 0


def cmd_run_canary(args):
    with Database(args.db) as db:
        print(dumps_json(CanaryService(db).run_canary(args.scope, tuple(args.golden_test_set_id), args.configuration_snapshot_id)))
    return 0


def cmd_show_canary_run(args):
    with Database(args.db) as db:
        repo = CanaryRepository(db)
        print(dumps_json({"run": repo.get_run(args.canary_run_id), "results": repo.list_results(args.canary_run_id)}))
    return 0


def cmd_export_canary_report(args):
    with Database(args.db) as db:
        writer = CanaryReportWriter(db)
        md = args.report_dir / f"canary_run_{args.canary_run_id}.md"
        js = args.report_dir / f"canary_run_{args.canary_run_id}.json"
        writer.write_markdown_report(args.canary_run_id, md)
        writer.write_json_report(args.canary_run_id, js)
        print(dumps_json({"markdown": md, "json": js}))
    return 0


def cmd_create_context_package(args):
    with Database(args.db) as db:
        print(dumps_json(ContextPackageService(db).create_package(args.name, args.scope, date.fromisoformat(args.as_of_date), args.summary_text, args.created_by)))
    return 0


def cmd_add_context_item(args):
    with Database(args.db) as db:
        print(dumps_json(ContextPackageService(db).add_item(args.context_package_id, args.item_type, args.item_id, args.role, args.title, args.summary)))
    return 0


def cmd_validate_context_package(args):
    with Database(args.db) as db:
        print(dumps_json(ContextPackageService(db).validate_package(args.context_package_id)))
    return 0


def cmd_export_context_package(args):
    with Database(args.db) as db:
        writer = ContextPackageReportWriter(db)
        md = args.report_dir / f"context_package_{args.context_package_id}.md"
        js = args.report_dir / f"context_package_{args.context_package_id}.json"
        writer.write_markdown_report(args.context_package_id, md)
        writer.write_json_report(args.context_package_id, js)
        print(dumps_json({"markdown": md, "json": js}))
    return 0


def cmd_create_delta_review(args):
    with Database(args.db) as db:
        print(dumps_json(DeltaReviewService(db).create_delta_review(args.name, args.previous_context_package_id, args.current_context_package_id, args.summary)))
    return 0


def cmd_create_memory_item(args):
    with Database(args.db) as db:
        print(dumps_json(MemoryService(db).create_memory_item(args.type, args.key, args.text, args.source_item_type, args.source_item_id, args.importance)))
    return 0


def cmd_list_memory_items(args):
    with Database(args.db) as db:
        print(dumps_json(MemoryService(db).list_memory_items(args.type)))
    return 0


def cmd_capture_system_health(args):
    with Database(args.db) as db:
        print(dumps_json(SystemHealthService(db).capture_health_snapshot(date.fromisoformat(args.as_of_date))))
    return 0


def cmd_export_system_health_report(args):
    with Database(args.db) as db:
        writer = SystemHealthReportWriter(db)
        md = args.report_dir / f"system_health_{args.system_health_snapshot_id}.md"
        js = args.report_dir / f"system_health_{args.system_health_snapshot_id}.json"
        writer.write_markdown_report(args.system_health_snapshot_id, md)
        writer.write_json_report(args.system_health_snapshot_id, js)
        print(dumps_json({"markdown": md, "json": js}))
    return 0


def cmd_register_read_only_source(args):
    with Database(args.db) as db:
        print(dumps_json(ReadOnlyIntegrationService(db).register_source(args.name, args.type, args.read_only_confirmed, args.authority_boundary_note, args.connection_descriptor_json)))
    return 0


def cmd_record_read_only_import(args):
    with Database(args.db) as db:
        print(dumps_json(ReadOnlyIntegrationService(db).record_import(args.integration_source_id, args.scope, args.status, args.artifact_path, args.rows_seen, args.rows_imported, args.checksum, args.notes)))
    return 0
