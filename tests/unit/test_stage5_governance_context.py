from __future__ import annotations

from datetime import date

import pytest

from portfolio_os.context import ContextPackageService, DeltaReviewService, MemoryService
from portfolio_os.context.report_writer import ContextPackageReportWriter
from portfolio_os.governance import (
    CanaryService,
    GoldenTestRepository,
    GovernancePolicyRepository,
    GovernancePolicyService,
    SystemHealthService,
    TemplateGovernanceService,
)
from portfolio_os.governance.default_policy import DEFAULT_GOVERNANCE_POLICY_NAME
from portfolio_os.integrations import ReadOnlyIntegrationService
from portfolio_os.senior import SeniorMemoInputBundleBuilder, SeniorMemoQAService, SeniorMemoService
from tests.unit.test_stage4_senior_memo import create_valid_macro_context, create_valid_research_packet, fill_valid_memo


def create_valid_senior_memo(db) -> int:
    research_id = create_valid_research_packet(db, "S5MEM")
    macro_id = create_valid_macro_context(db)
    bundle = SeniorMemoInputBundleBuilder(db).build_bundle(date(2026, 4, 1), (research_id,), macro_id)
    memo = SeniorMemoService(db).create_memo(bundle.input_bundle_id, "Stage 5 memo", "asset", "Executive summary reviewed.")
    fill_valid_memo(db, memo.senior_memo_id)
    SeniorMemoQAService(db).run_and_apply(memo.senior_memo_id)
    return memo.senior_memo_id


def test_default_governance_policy_seed_and_single_active(db) -> None:
    policy = GovernancePolicyService(db).seed_default_policy(activate=True)
    assert policy.policy_name == DEFAULT_GOVERNANCE_POLICY_NAME
    assert policy.policy_status == "active"
    rules = GovernancePolicyRepository(db).list_rules(policy.governance_policy_id)
    codes = {rule.rule_code for rule in rules}
    assert "NO_AUTHORITY_ESCALATION" in codes
    assert "READ_ONLY_INTEGRATION_ONLY" in codes

    again = GovernancePolicyService(db).seed_default_policy(activate=True)
    active_count = db.fetch_one("SELECT COUNT(*) AS count FROM governance_policies WHERE policy_status = 'active'")["count"]
    assert again.governance_policy_id == policy.governance_policy_id
    assert active_count == 1


def test_template_hash_and_activation_requires_canary_for_modified_template(db) -> None:
    service = TemplateGovernanceService(db)
    default_template = service.register_template("default_context", "context_package")
    default_version = service.create_template_version(default_template.template_id, "1.0.0", "default body", is_default=True)
    assert default_version.template_hash == service.hash_template("default body")
    assert service.activate_template_version(default_version.template_version_id).template_status == "active"

    custom_template = service.register_template("custom_context", "context_package")
    custom_version = service.create_template_version(custom_template.template_id, "1.0.0", "custom body")
    with pytest.raises(ValueError):
        service.activate_template_version(custom_version.template_version_id)

    golden = GoldenTestRepository(db).create_set("authority", "1")
    GoldenTestRepository(db).add_case(golden.golden_test_set_id, "forbidden text stays forbidden", "forbidden_authority_language", "buy now", "failed")
    assert CanaryService(db).run_canary("authority_boundary", (golden.golden_test_set_id,)).run_status == "passed"
    assert service.activate_template_version(custom_version.template_version_id).template_status == "active"


def test_golden_canary_authority_boundary_checks(db) -> None:
    golden = GoldenTestRepository(db).create_set("boundary", "1")
    GoldenTestRepository(db).add_case(golden.golden_test_set_id, "safe context", "valid_context_boundary", "This is review context only.", "passed")
    GoldenTestRepository(db).add_case(golden.golden_test_set_id, "forbidden order", "forbidden_authority_language", "execute order now", "failed")
    run = CanaryService(db).run_canary("authority_boundary", (golden.golden_test_set_id,))
    assert run.run_status == "passed"
    assert run.passed_count == 2

    mismatch = GoldenTestRepository(db).create_set("boundary_mismatch", "1")
    GoldenTestRepository(db).add_case(mismatch.golden_test_set_id, "wrong expectation", "forbidden_authority_language", "sell now", "passed")
    failed = CanaryService(db).run_canary("authority_boundary", (mismatch.golden_test_set_id,))
    assert failed.run_status == "failed"


def test_context_package_validates_upstream_artifacts_and_reports_authority_boundary(db, tmp_path) -> None:
    GovernancePolicyService(db).seed_default_policy(activate=True)
    research_id = create_valid_research_packet(db, "S5CTX")
    macro_id = create_valid_macro_context(db)
    senior_memo_id = create_valid_senior_memo(db)

    service = ContextPackageService(db)
    package = service.create_package("Valid context", "review", date(2026, 4, 1), "Context assembled.")
    service.add_item(package.context_package_id, "research_packet", research_id, item_summary="Valid research.")
    service.add_item(package.context_package_id, "macro_context", macro_id, item_summary="Valid macro.")
    service.add_item(package.context_package_id, "senior_memo", senior_memo_id, item_summary="Valid memo.")
    validated = service.validate_package(package.context_package_id)
    assert validated.package_status == "valid"

    report = ContextPackageReportWriter(db).write_markdown_report(package.context_package_id, tmp_path / "context.md")
    text = report.read_text(encoding="utf-8")
    assert "not order authority" in text
    assert "Order tickets are included only as context" in text


def test_context_package_rejects_invalid_upstream_and_invalid_item_types(db) -> None:
    package = ContextPackageService(db).create_package("Invalid context", "review", date(2026, 4, 1))
    with pytest.raises(ValueError):
        ContextPackageService(db).add_item(package.context_package_id, "instruction", 1)
    with pytest.raises(ValueError):
        ContextPackageService(db).add_item(package.context_package_id, "order_ticket", 1, "history")

    invalid_research_id = create_valid_research_packet(db, "S5BAD")
    db.execute("UPDATE research_packets SET packet_status = 'invalid', qa_status = 'failed' WHERE research_packet_id = ?", (invalid_research_id,))
    db.commit()
    ContextPackageService(db).add_item(package.context_package_id, "research_packet", invalid_research_id)
    validated = ContextPackageService(db).validate_package(package.context_package_id)
    assert validated.package_status == "invalid"


def test_context_budget_delta_memory_and_health_classification(db) -> None:
    GovernancePolicyService(db).seed_default_policy(activate=True)
    memory_service = MemoryService(db)
    package_service = ContextPackageService(db)
    package = package_service.create_package("Budget warning", "review", date(2026, 4, 1))
    for idx in range(41):
        memory = memory_service.create_memory_item("system_note", f"budget_{idx}", "Memory context item.")
        package_service.add_item(package.context_package_id, "memory", memory.memory_item_id)
    validated = package_service.validate_package(package.context_package_id)
    assert validated.package_status == "valid"
    assert validated.budget_status == "warning"
    assert len(memory_service.list_memory_items()) == 41

    other = package_service.create_package("Budget compare", "review", date(2026, 4, 1))
    review = DeltaReviewService(db).create_delta_review("Delta", package.context_package_id, other.context_package_id)
    assert review.review_status == "complete"

    yellow = SystemHealthService(db).capture_health_snapshot(date(2026, 4, 1))
    assert yellow.health_status == "yellow"
    db.execute(
        """
        INSERT INTO reconciliation_snapshots(as_of_date, started_at, completed_at, ledger_status_before, ledger_status_after,
        reconciliation_status, snapshot_source)
        VALUES ('2026-04-01', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'), 'provisional', 'reconciled', 'passed', 'manual')
        """
    )
    db.commit()
    green = SystemHealthService(db).capture_health_snapshot(date(2026, 4, 1))
    assert green.health_status in {"green", "yellow"}


def test_read_only_source_rejects_unconfirmed_write_authority(db) -> None:
    service = ReadOnlyIntegrationService(db)
    with pytest.raises(ValueError):
        service.register_source("Broker write API", "broker_export", False, "Not confirmed read-only.")
    source = service.register_source("Broker export", "broker_export", True, "CSV export only; no broker write capability.")
    run = service.record_import(source.integration_source_id, "snapshot", "recorded", rows_seen=10, rows_imported=0)
    assert source.read_only_confirmed is True
    assert run.rows_seen == 10
