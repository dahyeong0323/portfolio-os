from __future__ import annotations

from datetime import date

from portfolio_os.context import ContextPackageService
from portfolio_os.context.report_writer import ContextPackageReportWriter
from portfolio_os.governance import (
    CanaryService,
    ConfigurationSnapshotService,
    GoldenTestRepository,
    GovernancePolicyService,
    SystemHealthService,
)
from portfolio_os.governance.report_writer import CanaryReportWriter, GovernanceReportWriter, SystemHealthReportWriter
from portfolio_os.integrations import ReadOnlyIntegrationService
from portfolio_os.senior import SeniorMemoInputBundleBuilder, SeniorMemoQAService, SeniorMemoService
from tests.unit.test_stage4_senior_memo import create_valid_macro_context, create_valid_research_packet, fill_valid_memo


def test_stage5_full_flow_generates_reports(db, tmp_path) -> None:
    policy = GovernancePolicyService(db).seed_default_policy(activate=True)
    config = ConfigurationSnapshotService(db).capture_snapshot("stage5 config", date(2026, 5, 1))
    golden = GoldenTestRepository(db).create_set("stage5 authority", "1")
    GoldenTestRepository(db).add_case(golden.golden_test_set_id, "context only", "valid_context_boundary", "This package is context only.", "passed")
    canary = CanaryService(db).run_canary("system", (golden.golden_test_set_id,), config.configuration_snapshot_id)

    research_id = create_valid_research_packet(db, "S5FLOW")
    macro_id = create_valid_macro_context(db)
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 5, 1), (research_id,), macro_id)
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Stage 5 flow memo", "asset", "Executive summary reviewed.")
    fill_valid_memo(db, memo.senior_memo_id)
    SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)

    package = ContextPackageService(db).create_package("Stage 5 package", "review", date(2026, 5, 1))
    ContextPackageService(db).add_item(package.context_package_id, "research_packet", research_id)
    ContextPackageService(db).add_item(package.context_package_id, "macro_context", macro_id)
    ContextPackageService(db).add_item(package.context_package_id, "senior_memo", memo.senior_memo_id)
    validated = ContextPackageService(db).validate_package(package.context_package_id)
    assert validated.package_status == "valid"

    health = SystemHealthService(db).capture_health_snapshot(date(2026, 5, 1))
    source = ReadOnlyIntegrationService(db).register_source("Read-only statement export", "broker_export", True, "Read-only CSV statement export.")
    import_run = ReadOnlyIntegrationService(db).record_import(source.integration_source_id, "statement", "recorded", rows_seen=3)

    GovernanceReportWriter(db).write_policy_report(policy.governance_policy_id, tmp_path / "governance.md")
    GovernanceReportWriter(db).write_policy_json(policy.governance_policy_id, tmp_path / "governance.json")
    CanaryReportWriter(db).write_markdown_report(canary.canary_run_id, tmp_path / "canary.md")
    CanaryReportWriter(db).write_json_report(canary.canary_run_id, tmp_path / "canary.json")
    ContextPackageReportWriter(db).write_markdown_report(package.context_package_id, tmp_path / "context.md")
    ContextPackageReportWriter(db).write_json_report(package.context_package_id, tmp_path / "context.json")
    SystemHealthReportWriter(db).write_markdown_report(health.system_health_snapshot_id, tmp_path / "health.md")
    SystemHealthReportWriter(db).write_json_report(health.system_health_snapshot_id, tmp_path / "health.json")

    assert canary.run_status == "passed"
    assert import_run.rows_seen == 3
    for name in ("governance.md", "governance.json", "canary.md", "canary.json", "context.md", "context.json", "health.md", "health.json"):
        assert (tmp_path / name).exists()


def test_stage5_rejects_invalid_upstream_artifact(db) -> None:
    package = ContextPackageService(db).create_package("Reject invalid", "review", date(2026, 5, 1))
    invalid_research_id = create_valid_research_packet(db, "S5INV")
    db.execute("UPDATE research_packets SET packet_status = 'invalid', qa_status = 'failed' WHERE research_packet_id = ?", (invalid_research_id,))
    db.commit()
    ContextPackageService(db).add_item(package.context_package_id, "research_packet", invalid_research_id)
    validated = ContextPackageService(db).validate_package(package.context_package_id)
    assert validated.package_status == "invalid"
