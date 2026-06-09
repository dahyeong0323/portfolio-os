from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any, Sequence

from portfolio_os.db.connection import Database
from portfolio_os.governance.models import (
    CanaryResult,
    CanaryRun,
    ConfigurationSnapshot,
    GoldenTestCase,
    GoldenTestSet,
    GovernanceAuditEvent,
    GovernancePolicy,
    GovernancePolicyRule,
    SystemHealthSnapshot,
    TemplateRegistryEntry,
    TemplateVersion,
)
from portfolio_os.serialization import dumps_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, require_text


def _bool(value: Any) -> bool:
    return bool(int(value))


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def policy_from_row(row: dict[str, Any]) -> GovernancePolicy:
    return GovernancePolicy(
        row["governance_policy_id"],
        row["policy_name"],
        row["version"],
        row["policy_status"],
        row["description"],
        _bool(row["canary_required_before_activation"]),
        _dt(row["created_at"]),
        _dt(row["activated_at"]),
        _dt(row["retired_at"]),
    )


def rule_from_row(row: dict[str, Any]) -> GovernancePolicyRule:
    return GovernancePolicyRule(
        row["governance_rule_id"],
        row["governance_policy_id"],
        row["rule_code"],
        row["rule_scope"],
        row["rule_value"],
        row["threshold_value"],
        row["severity"],
        _bool(row["is_active"]),
        row["description"],
        _dt(row["created_at"]),
    )


def config_from_row(row: dict[str, Any]) -> ConfigurationSnapshot:
    return ConfigurationSnapshot(
        row["configuration_snapshot_id"],
        row["snapshot_name"],
        row["snapshot_scope"],
        date_from_text(row["as_of_date"]),
        row["stage_versions_json"],
        row["active_risk_policy_id"],
        row["active_governance_policy_id"],
        row["active_template_version_ids_json"],
        row["configuration_json"],
        row["snapshot_digest"],
        _dt(row["created_at"]),
    )


def template_from_row(row: dict[str, Any]) -> TemplateRegistryEntry:
    return TemplateRegistryEntry(
        row["template_id"],
        row["template_name"],
        row["template_type"],
        row["template_scope"],
        row["description"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def template_version_from_row(row: dict[str, Any]) -> TemplateVersion:
    return TemplateVersion(
        row["template_version_id"],
        row["template_id"],
        row["version"],
        row["template_status"],
        row["template_body"],
        row["template_hash"],
        _bool(row["is_default"]),
        _bool(row["requires_canary"]),
        _dt(row["created_at"]),
        _dt(row["activated_at"]),
        _dt(row["retired_at"]),
    )


def golden_set_from_row(row: dict[str, Any]) -> GoldenTestSet:
    return GoldenTestSet(row["golden_test_set_id"], row["set_name"], row["set_version"], row["test_scope"], row["description"], _bool(row["is_active"]), _dt(row["created_at"]))


def golden_case_from_row(row: dict[str, Any]) -> GoldenTestCase:
    return GoldenTestCase(row["golden_test_case_id"], row["golden_test_set_id"], row["case_name"], row["case_type"], row["input_text"], row["expected_status"], row["expected_reason"], _bool(row["is_active"]), _dt(row["created_at"]))


def canary_run_from_row(row: dict[str, Any]) -> CanaryRun:
    return CanaryRun(
        row["canary_run_id"],
        row["run_scope"],
        row["run_status"],
        row["governance_policy_id"],
        row["configuration_snapshot_id"],
        row["golden_test_set_ids_json"],
        row["passed_count"],
        row["failed_count"],
        row["warning_count"],
        row["summary_text"],
        _dt(row["created_at"]),
        _dt(row["completed_at"]),
    )


def canary_result_from_row(row: dict[str, Any]) -> CanaryResult:
    return CanaryResult(row["canary_result_id"], row["canary_run_id"], row["golden_test_case_id"], row["check_code"], row["result_status"], row["severity"], row["result_summary"], row["evidence_json"], _dt(row["created_at"]))


def health_from_row(row: dict[str, Any]) -> SystemHealthSnapshot:
    return SystemHealthSnapshot(
        row["system_health_snapshot_id"],
        date_from_text(row["as_of_date"]),
        row["health_status"],
        row["ledger_status"],
        row["latest_reconciliation_status"],
        row["latest_canary_status"],
        row["open_ticket_count"],
        row["pending_execution_count"],
        row["open_override_count"],
        row["invalid_research_count"],
        row["invalid_macro_count"],
        row["invalid_senior_memo_count"],
        row["warning_count"],
        row["failure_count"],
        row["health_json"],
        _dt(row["created_at"]),
    )


def audit_event_from_row(row: dict[str, Any]) -> GovernanceAuditEvent:
    return GovernanceAuditEvent(row["governance_audit_event_id"], row["event_type"], row["event_scope"], row["severity"], row["related_table"], row["related_id"], row["event_summary"], row["event_payload_json"], _dt(row["created_at"]))


class GovernancePolicyRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_policy(self, policy_name: str, version: str, description: str | None = None, canary_required_before_activation: bool = True) -> GovernancePolicy:
        require_text(policy_name, "policy_name")
        require_text(version, "version")
        cursor = self.db.execute(
            """
            INSERT INTO governance_policies(policy_name, version, description, canary_required_before_activation)
            VALUES (?, ?, ?, ?)
            """,
            (policy_name, version, description, int(canary_required_before_activation)),
        )
        self.db.commit()
        return self.get_policy(cursor.lastrowid)

    def find_policy(self, policy_name: str, version: str) -> GovernancePolicy | None:
        row = self.db.fetch_one("SELECT * FROM governance_policies WHERE policy_name = ? AND version = ?", (policy_name, version))
        return policy_from_row(row) if row else None

    def get_policy(self, governance_policy_id: int) -> GovernancePolicy:
        row = self.db.fetch_one("SELECT * FROM governance_policies WHERE governance_policy_id = ?", (governance_policy_id,))
        if row is None:
            raise ValueError(f"governance policy not found: {governance_policy_id}")
        return policy_from_row(row)

    def active_policy(self) -> GovernancePolicy | None:
        row = self.db.fetch_one("SELECT * FROM governance_policies WHERE policy_status = 'active' LIMIT 1")
        return policy_from_row(row) if row else None

    def activate_policy(self, governance_policy_id: int) -> GovernancePolicy:
        self.db.execute("UPDATE governance_policies SET policy_status = 'retired', retired_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE policy_status = 'active' AND governance_policy_id != ?", (governance_policy_id,))
        self.db.execute("UPDATE governance_policies SET policy_status = 'active', activated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now'), retired_at = NULL WHERE governance_policy_id = ?", (governance_policy_id,))
        self.db.commit()
        return self.get_policy(governance_policy_id)

    def add_rule(self, governance_policy_id: int, rule_code: str, rule_scope: str, rule_value: str, threshold_value: str | None = None, severity: str = "hard_block", description: str | None = None) -> GovernancePolicyRule:
        cursor = self.db.execute(
            """
            INSERT INTO governance_policy_rules(governance_policy_id, rule_code, rule_scope, rule_value, threshold_value, severity, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (governance_policy_id, rule_code, rule_scope, rule_value, threshold_value, severity, description),
        )
        self.db.commit()
        return self.get_rule(cursor.lastrowid)

    def get_rule(self, governance_rule_id: int) -> GovernancePolicyRule:
        row = self.db.fetch_one("SELECT * FROM governance_policy_rules WHERE governance_rule_id = ?", (governance_rule_id,))
        if row is None:
            raise ValueError(f"governance rule not found: {governance_rule_id}")
        return rule_from_row(row)

    def list_rules(self, governance_policy_id: int | None = None) -> list[GovernancePolicyRule]:
        if governance_policy_id is None:
            policy = self.active_policy()
            if policy is None:
                return []
            governance_policy_id = policy.governance_policy_id
        return [rule_from_row(row) for row in self.db.fetch_all("SELECT * FROM governance_policy_rules WHERE governance_policy_id = ? AND is_active = 1 ORDER BY governance_rule_id", (governance_policy_id,))]


class ConfigurationSnapshotRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_snapshot(self, snapshot_name: str, snapshot_scope: str, as_of_date: date, stage_versions_json: str, active_risk_policy_id: int | None, active_governance_policy_id: int | None, active_template_version_ids_json: str, configuration_json: str, snapshot_digest: str) -> ConfigurationSnapshot:
        cursor = self.db.execute(
            """
            INSERT INTO configuration_snapshots(snapshot_name, snapshot_scope, as_of_date, stage_versions_json,
            active_risk_policy_id, active_governance_policy_id, active_template_version_ids_json, configuration_json, snapshot_digest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_name, snapshot_scope, date_to_text(as_of_date), stage_versions_json, active_risk_policy_id, active_governance_policy_id, active_template_version_ids_json, configuration_json, snapshot_digest),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, configuration_snapshot_id: int) -> ConfigurationSnapshot:
        row = self.db.fetch_one("SELECT * FROM configuration_snapshots WHERE configuration_snapshot_id = ?", (configuration_snapshot_id,))
        if row is None:
            raise ValueError(f"configuration snapshot not found: {configuration_snapshot_id}")
        return config_from_row(row)

    def latest(self) -> ConfigurationSnapshot | None:
        row = self.db.fetch_one("SELECT * FROM configuration_snapshots ORDER BY configuration_snapshot_id DESC LIMIT 1")
        return config_from_row(row) if row else None


class TemplateRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def register_template(self, template_name: str, template_type: str, template_scope: str = "stage5", description: str | None = None) -> TemplateRegistryEntry:
        require_text(template_name, "template_name")
        cursor = self.db.execute(
            "INSERT INTO template_registry(template_name, template_type, template_scope, description) VALUES (?, ?, ?, ?)",
            (template_name, template_type, template_scope, description),
        )
        self.db.commit()
        return self.get_template(cursor.lastrowid)

    def get_template(self, template_id: int) -> TemplateRegistryEntry:
        row = self.db.fetch_one("SELECT * FROM template_registry WHERE template_id = ?", (template_id,))
        if row is None:
            raise ValueError(f"template not found: {template_id}")
        return template_from_row(row)

    def find_template(self, template_name: str) -> TemplateRegistryEntry | None:
        row = self.db.fetch_one("SELECT * FROM template_registry WHERE template_name = ?", (template_name,))
        return template_from_row(row) if row else None

    def create_version(self, template_id: int, version: str, template_body: str, template_hash: str, is_default: bool = False, requires_canary: bool = True) -> TemplateVersion:
        require_text(template_body, "template_body")
        cursor = self.db.execute(
            """
            INSERT INTO template_versions(template_id, version, template_body, template_hash, is_default, requires_canary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (template_id, version, template_body, template_hash, int(is_default), int(requires_canary)),
        )
        self.db.commit()
        return self.get_version(cursor.lastrowid)

    def get_version(self, template_version_id: int) -> TemplateVersion:
        row = self.db.fetch_one("SELECT * FROM template_versions WHERE template_version_id = ?", (template_version_id,))
        if row is None:
            raise ValueError(f"template version not found: {template_version_id}")
        return template_version_from_row(row)

    def active_version(self, template_id: int) -> TemplateVersion | None:
        row = self.db.fetch_one("SELECT * FROM template_versions WHERE template_id = ? AND template_status = 'active' LIMIT 1", (template_id,))
        return template_version_from_row(row) if row else None

    def activate_version(self, template_version_id: int) -> TemplateVersion:
        version = self.get_version(template_version_id)
        self.db.execute("UPDATE template_versions SET template_status = 'retired', retired_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE template_id = ? AND template_status = 'active' AND template_version_id != ?", (version.template_id, template_version_id))
        self.db.execute("UPDATE template_versions SET template_status = 'active', activated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now'), retired_at = NULL WHERE template_version_id = ?", (template_version_id,))
        self.db.commit()
        return self.get_version(template_version_id)

    def list_active_versions(self) -> list[TemplateVersion]:
        return [template_version_from_row(row) for row in self.db.fetch_all("SELECT * FROM template_versions WHERE template_status = 'active' ORDER BY template_version_id")]


class GoldenTestRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_set(self, set_name: str, set_version: str, test_scope: str = "authority_boundary", description: str | None = None) -> GoldenTestSet:
        cursor = self.db.execute(
            "INSERT INTO golden_test_sets(set_name, set_version, test_scope, description) VALUES (?, ?, ?, ?)",
            (set_name, set_version, test_scope, description),
        )
        self.db.commit()
        return self.get_set(cursor.lastrowid)

    def get_set(self, golden_test_set_id: int) -> GoldenTestSet:
        row = self.db.fetch_one("SELECT * FROM golden_test_sets WHERE golden_test_set_id = ?", (golden_test_set_id,))
        if row is None:
            raise ValueError(f"golden test set not found: {golden_test_set_id}")
        return golden_set_from_row(row)

    def add_case(self, golden_test_set_id: int, case_name: str, case_type: str, input_text: str, expected_status: str, expected_reason: str | None = None) -> GoldenTestCase:
        cursor = self.db.execute(
            """
            INSERT INTO golden_test_cases(golden_test_set_id, case_name, case_type, input_text, expected_status, expected_reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (golden_test_set_id, case_name, case_type, input_text, expected_status, expected_reason),
        )
        self.db.commit()
        return self.get_case(cursor.lastrowid)

    def get_case(self, golden_test_case_id: int) -> GoldenTestCase:
        row = self.db.fetch_one("SELECT * FROM golden_test_cases WHERE golden_test_case_id = ?", (golden_test_case_id,))
        if row is None:
            raise ValueError(f"golden test case not found: {golden_test_case_id}")
        return golden_case_from_row(row)

    def list_cases(self, golden_test_set_ids: Sequence[int] = ()) -> list[GoldenTestCase]:
        if golden_test_set_ids:
            placeholders = ",".join("?" for _ in golden_test_set_ids)
            rows = self.db.fetch_all(f"SELECT * FROM golden_test_cases WHERE golden_test_set_id IN ({placeholders}) AND is_active = 1 ORDER BY golden_test_case_id", tuple(golden_test_set_ids))
        else:
            rows = self.db.fetch_all("SELECT * FROM golden_test_cases WHERE is_active = 1 ORDER BY golden_test_case_id")
        return [golden_case_from_row(row) for row in rows]


class CanaryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_run(self, run_scope: str, governance_policy_id: int | None, configuration_snapshot_id: int | None, golden_test_set_ids: Sequence[int]) -> CanaryRun:
        cursor = self.db.execute(
            """
            INSERT INTO canary_runs(run_scope, governance_policy_id, configuration_snapshot_id, golden_test_set_ids_json)
            VALUES (?, ?, ?, ?)
            """,
            (run_scope, governance_policy_id, configuration_snapshot_id, dumps_json(tuple(golden_test_set_ids))),
        )
        self.db.commit()
        return self.get_run(cursor.lastrowid)

    def add_result(self, result: CanaryResult) -> CanaryResult:
        cursor = self.db.execute(
            """
            INSERT INTO canary_results(canary_run_id, golden_test_case_id, check_code, result_status, severity, result_summary, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (result.canary_run_id, result.golden_test_case_id, result.check_code, result.result_status, result.severity, result.result_summary, result.evidence_json),
        )
        self.db.commit()
        return replace(result, canary_result_id=cursor.lastrowid)

    def complete_run(self, canary_run_id: int, run_status: str, passed_count: int, failed_count: int, warning_count: int, summary_text: str) -> CanaryRun:
        self.db.execute(
            """
            UPDATE canary_runs
            SET run_status = ?, passed_count = ?, failed_count = ?, warning_count = ?, summary_text = ?,
                completed_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
            WHERE canary_run_id = ?
            """,
            (run_status, passed_count, failed_count, warning_count, summary_text, canary_run_id),
        )
        self.db.commit()
        return self.get_run(canary_run_id)

    def get_run(self, canary_run_id: int) -> CanaryRun:
        row = self.db.fetch_one("SELECT * FROM canary_runs WHERE canary_run_id = ?", (canary_run_id,))
        if row is None:
            raise ValueError(f"canary run not found: {canary_run_id}")
        return canary_run_from_row(row)

    def get_latest_run(self) -> CanaryRun | None:
        row = self.db.fetch_one("SELECT * FROM canary_runs ORDER BY canary_run_id DESC LIMIT 1")
        return canary_run_from_row(row) if row else None

    def latest_passed_run(self) -> CanaryRun | None:
        row = self.db.fetch_one("SELECT * FROM canary_runs WHERE run_status = 'passed' ORDER BY canary_run_id DESC LIMIT 1")
        return canary_run_from_row(row) if row else None

    def list_results(self, canary_run_id: int) -> list[CanaryResult]:
        return [canary_result_from_row(row) for row in self.db.fetch_all("SELECT * FROM canary_results WHERE canary_run_id = ? ORDER BY canary_result_id", (canary_run_id,))]


class SystemHealthRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, snapshot: SystemHealthSnapshot) -> SystemHealthSnapshot:
        cursor = self.db.execute(
            """
            INSERT INTO system_health_snapshots(as_of_date, health_status, ledger_status, latest_reconciliation_status,
            latest_canary_status, open_ticket_count, pending_execution_count, open_override_count, invalid_research_count,
            invalid_macro_count, invalid_senior_memo_count, warning_count, failure_count, health_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_to_text(snapshot.as_of_date),
                snapshot.health_status,
                snapshot.ledger_status,
                snapshot.latest_reconciliation_status,
                snapshot.latest_canary_status,
                snapshot.open_ticket_count,
                snapshot.pending_execution_count,
                snapshot.open_override_count,
                snapshot.invalid_research_count,
                snapshot.invalid_macro_count,
                snapshot.invalid_senior_memo_count,
                snapshot.warning_count,
                snapshot.failure_count,
                snapshot.health_json,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, system_health_snapshot_id: int) -> SystemHealthSnapshot:
        row = self.db.fetch_one("SELECT * FROM system_health_snapshots WHERE system_health_snapshot_id = ?", (system_health_snapshot_id,))
        if row is None:
            raise ValueError(f"system health snapshot not found: {system_health_snapshot_id}")
        return health_from_row(row)

    def latest(self) -> SystemHealthSnapshot | None:
        row = self.db.fetch_one("SELECT * FROM system_health_snapshots ORDER BY system_health_snapshot_id DESC LIMIT 1")
        return health_from_row(row) if row else None


class GovernanceAuditRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_event(self, event_type: str, event_scope: str, severity: str, event_summary: str, related_table: str | None = None, related_id: int | None = None, event_payload_json: str = "{}") -> GovernanceAuditEvent:
        cursor = self.db.execute(
            """
            INSERT INTO governance_audit_events(event_type, event_scope, severity, related_table, related_id, event_summary, event_payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_type, event_scope, severity, related_table, related_id, event_summary, event_payload_json),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, governance_audit_event_id: int) -> GovernanceAuditEvent:
        row = self.db.fetch_one("SELECT * FROM governance_audit_events WHERE governance_audit_event_id = ?", (governance_audit_event_id,))
        if row is None:
            raise ValueError(f"governance audit event not found: {governance_audit_event_id}")
        return audit_event_from_row(row)
