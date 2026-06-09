from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class GovernancePolicy:
    governance_policy_id: int
    policy_name: str
    version: str
    policy_status: str
    description: str | None
    canary_required_before_activation: bool
    created_at: datetime | None
    activated_at: datetime | None
    retired_at: datetime | None


@dataclass(frozen=True)
class GovernancePolicyRule:
    governance_rule_id: int
    governance_policy_id: int
    rule_code: str
    rule_scope: str
    rule_value: str
    threshold_value: str | None
    severity: str
    is_active: bool
    description: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class ConfigurationSnapshot:
    configuration_snapshot_id: int
    snapshot_name: str
    snapshot_scope: str
    as_of_date: date
    stage_versions_json: str
    active_risk_policy_id: int | None
    active_governance_policy_id: int | None
    active_template_version_ids_json: str
    configuration_json: str
    snapshot_digest: str
    created_at: datetime | None


@dataclass(frozen=True)
class TemplateRegistryEntry:
    template_id: int
    template_name: str
    template_type: str
    template_scope: str
    description: str | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class TemplateVersion:
    template_version_id: int
    template_id: int
    version: str
    template_status: str
    template_body: str
    template_hash: str
    is_default: bool
    requires_canary: bool
    created_at: datetime | None
    activated_at: datetime | None
    retired_at: datetime | None


@dataclass(frozen=True)
class GoldenTestSet:
    golden_test_set_id: int
    set_name: str
    set_version: str
    test_scope: str
    description: str | None
    is_active: bool
    created_at: datetime | None


@dataclass(frozen=True)
class GoldenTestCase:
    golden_test_case_id: int
    golden_test_set_id: int
    case_name: str
    case_type: str
    input_text: str
    expected_status: str
    expected_reason: str | None
    is_active: bool
    created_at: datetime | None


@dataclass(frozen=True)
class CanaryRun:
    canary_run_id: int
    run_scope: str
    run_status: str
    governance_policy_id: int | None
    configuration_snapshot_id: int | None
    golden_test_set_ids_json: str
    passed_count: int
    failed_count: int
    warning_count: int
    summary_text: str | None
    created_at: datetime | None
    completed_at: datetime | None


@dataclass(frozen=True)
class CanaryResult:
    canary_result_id: int
    canary_run_id: int
    golden_test_case_id: int | None
    check_code: str
    result_status: str
    severity: str
    result_summary: str
    evidence_json: str
    created_at: datetime | None


@dataclass(frozen=True)
class SystemHealthSnapshot:
    system_health_snapshot_id: int
    as_of_date: date
    health_status: str
    ledger_status: str | None
    latest_reconciliation_status: str | None
    latest_canary_status: str | None
    open_ticket_count: int
    pending_execution_count: int
    open_override_count: int
    invalid_research_count: int
    invalid_macro_count: int
    invalid_senior_memo_count: int
    warning_count: int
    failure_count: int
    health_json: str
    created_at: datetime | None


@dataclass(frozen=True)
class GovernanceAuditEvent:
    governance_audit_event_id: int
    event_type: str
    event_scope: str
    severity: str
    related_table: str | None
    related_id: int | None
    event_summary: str
    event_payload_json: str
    created_at: datetime | None
