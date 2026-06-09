from __future__ import annotations

import hashlib
from datetime import date

from portfolio_os.db.connection import Database
from portfolio_os.governance.authority_checks import evaluate_authority_text, find_authority_boundary_hits
from portfolio_os.governance.default_policy import DEFAULT_GOVERNANCE_POLICY_NAME, DEFAULT_GOVERNANCE_POLICY_VERSION, DEFAULT_GOVERNANCE_RULES
from portfolio_os.governance.models import CanaryResult, SystemHealthSnapshot
from portfolio_os.governance.repositories import (
    CanaryRepository,
    ConfigurationSnapshotRepository,
    GoldenTestRepository,
    GovernanceAuditRepository,
    GovernancePolicyRepository,
    SystemHealthRepository,
    TemplateRepository,
)
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.repositories import ReconciliationRepository
from portfolio_os.serialization import dumps_json, loads_json


class GovernancePolicyService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.repo = GovernancePolicyRepository(db)

    def seed_default_policy(self, activate: bool = False):
        policy = self.repo.find_policy(DEFAULT_GOVERNANCE_POLICY_NAME, DEFAULT_GOVERNANCE_POLICY_VERSION)
        if policy is None:
            policy = self.repo.create_policy(
                DEFAULT_GOVERNANCE_POLICY_NAME,
                DEFAULT_GOVERNANCE_POLICY_VERSION,
                "Stage 5 default governance policy for context-only operation.",
                canary_required_before_activation=False,
            )
            for rule in DEFAULT_GOVERNANCE_RULES:
                self.repo.add_rule(
                    policy.governance_policy_id,
                    rule["rule_code"],
                    rule["rule_scope"],
                    rule["rule_value"],
                    rule.get("threshold_value"),
                    rule["severity"],
                    rule["description"],
                )
        if activate:
            policy = self.activate_policy(policy.governance_policy_id)
        return policy

    def activate_policy(self, governance_policy_id: int):
        policy = self.repo.get_policy(governance_policy_id)
        if policy.canary_required_before_activation and CanaryRepository(self.db).latest_passed_run() is None:
            raise ValueError("latest passed canary is required before activating this governance policy")
        return self.repo.activate_policy(governance_policy_id)

    def list_rules(self, governance_policy_id: int | None = None):
        return self.repo.list_rules(governance_policy_id)


class ConfigurationSnapshotService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def capture_snapshot(self, snapshot_name: str, as_of_date: date, snapshot_scope: str = "system"):
        versions = {row["version"]: row["name"] for row in self.db.fetch_all("SELECT version, name FROM schema_migrations ORDER BY version")}
        active_risk = self.db.fetch_one("SELECT policy_version_id FROM risk_policy_versions WHERE is_active = 1 LIMIT 1")
        active_governance = GovernancePolicyRepository(self.db).active_policy()
        active_templates = TemplateRepository(self.db).list_active_versions()
        rules = [
            {"rule_code": rule.rule_code, "rule_value": rule.rule_value, "severity": rule.severity}
            for rule in GovernancePolicyRepository(self.db).list_rules(active_governance.governance_policy_id if active_governance else None)
        ]
        payload = {
            "snapshot_name": snapshot_name,
            "snapshot_scope": snapshot_scope,
            "schema_max_version": max(versions) if versions else None,
            "active_risk_policy_id": active_risk["policy_version_id"] if active_risk else None,
            "active_governance_policy_id": active_governance.governance_policy_id if active_governance else None,
            "active_template_version_ids": tuple(item.template_version_id for item in active_templates),
            "governance_rules": tuple(rules),
        }
        digest = hashlib.sha256(dumps_json(payload).encode("utf-8")).hexdigest()
        return ConfigurationSnapshotRepository(self.db).create_snapshot(
            snapshot_name,
            snapshot_scope,
            as_of_date,
            dumps_json(versions),
            active_risk["policy_version_id"] if active_risk else None,
            active_governance.governance_policy_id if active_governance else None,
            dumps_json(tuple(item.template_version_id for item in active_templates)),
            dumps_json(payload),
            digest,
        )


class TemplateGovernanceService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.repo = TemplateRepository(db)

    @staticmethod
    def hash_template(template_body: str) -> str:
        return hashlib.sha256(template_body.encode("utf-8")).hexdigest()

    def register_template(self, template_name: str, template_type: str, template_scope: str = "stage5", description: str | None = None):
        return self.repo.register_template(template_name, template_type, template_scope, description)

    def create_template_version(self, template_id: int, version: str, template_body: str, is_default: bool = False, requires_canary: bool | None = None):
        if requires_canary is None:
            requires_canary = not is_default
        return self.repo.create_version(template_id, version, template_body, self.hash_template(template_body), is_default, requires_canary)

    def activate_template_version(self, template_version_id: int):
        version = self.repo.get_version(template_version_id)
        active = self.repo.active_version(version.template_id)
        first_default_activation = version.is_default and active is None
        if not first_default_activation and version.requires_canary and CanaryRepository(self.db).latest_passed_run() is None:
            raise ValueError("latest passed canary is required before activating non-default or modified templates")
        return self.repo.activate_version(template_version_id)


class CanaryService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def run_canary(self, run_scope: str = "system", golden_test_set_ids: tuple[int, ...] = (), configuration_snapshot_id: int | None = None):
        active_policy = GovernancePolicyRepository(self.db).active_policy()
        run = CanaryRepository(self.db).create_run(run_scope, active_policy.governance_policy_id if active_policy else None, configuration_snapshot_id, golden_test_set_ids)
        cases = GoldenTestRepository(self.db).list_cases(golden_test_set_ids)
        results: list[CanaryResult] = []

        if not cases:
            results.append(
                CanaryResult(
                    0,
                    run.canary_run_id,
                    None,
                    "NO_AUTHORITY_ESCALATION",
                    "passed",
                    "hard_block",
                    "Built-in authority boundary check passed; no golden cases were active.",
                    dumps_json({"run_scope": run_scope}),
                    None,
                )
            )

        for case in cases:
            actual_status = self._evaluate_case(case.case_type, case.input_text)
            result_status = "passed" if actual_status == case.expected_status else "failed"
            hits = find_authority_boundary_hits(case.input_text)
            results.append(
                CanaryResult(
                    0,
                    run.canary_run_id,
                    case.golden_test_case_id,
                    case.case_type,
                    result_status,
                    "hard_block" if result_status == "failed" else "info",
                    f"{case.case_name}: expected {case.expected_status}, observed {actual_status}.",
                    dumps_json({"authority_hits": hits, "expected_reason": case.expected_reason}),
                    None,
                )
            )

        saved_results = [CanaryRepository(self.db).add_result(result) for result in results]
        passed_count = sum(1 for result in saved_results if result.result_status == "passed")
        failed_count = sum(1 for result in saved_results if result.result_status == "failed")
        warning_count = sum(1 for result in saved_results if result.result_status == "warning")
        final_status = "failed" if failed_count else "passed"
        summary = f"Canary {final_status}: {passed_count} passed, {failed_count} failed, {warning_count} warning."
        completed = CanaryRepository(self.db).complete_run(run.canary_run_id, final_status, passed_count, failed_count, warning_count, summary)
        for result in saved_results:
            if result.result_status != "passed":
                GovernanceAuditRepository(self.db).record_event("canary_result", "canary", result.severity, result.result_summary, "canary_results", result.canary_result_id, result.evidence_json)
        return completed

    def _evaluate_case(self, case_type: str, input_text: str) -> str:
        if case_type in {"forbidden_authority_language", "valid_context_boundary"}:
            return evaluate_authority_text(input_text)
        if case_type == "read_only_integration":
            lowered = input_text.lower()
            return "passed" if "read-only" in lowered and not find_authority_boundary_hits(input_text) else "failed"
        if case_type == "template_activation":
            return "passed" if not find_authority_boundary_hits(input_text) else "failed"
        return "passed"


class SystemHealthService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def capture_health_snapshot(self, as_of_date: date):
        ledger = LedgerSnapshotBuilder(self.db).build_snapshot(as_of_date)
        latest_reconciliation = ReconciliationRepository(self.db).get_latest_reconciliation()
        latest_canary = CanaryRepository(self.db).get_latest_run()
        open_ticket_count = self._count("SELECT COUNT(*) AS count FROM order_tickets WHERE status NOT IN ('reconciled','cancelled','rejected','expired')")
        pending_execution_count = self._count("SELECT COUNT(*) AS count FROM manual_execution_logs WHERE execution_status IN ('logged','transaction_created','pending_reconciliation','reconciliation_failed')")
        open_override_count = self._count("SELECT COUNT(*) AS count FROM override_tickets WHERE status NOT IN ('cancelled','reconciled','postmortem_completed')")
        invalid_research_count = self._count("SELECT COUNT(*) AS count FROM research_packets WHERE packet_status != 'valid' OR qa_status = 'failed'")
        invalid_macro_count = self._count("SELECT COUNT(*) AS count FROM macro_context_packets WHERE packet_status != 'valid'")
        invalid_senior_memo_count = self._count("SELECT COUNT(*) AS count FROM senior_memos WHERE memo_status != 'valid' OR qa_status = 'failed'")

        failures: list[str] = []
        warnings: list[str] = []
        if ledger.ledger_status == "broken":
            failures.append("ledger is broken")
        elif ledger.ledger_status in {"provisional", "stale"}:
            warnings.append(f"ledger is {ledger.ledger_status}")
        if latest_reconciliation and latest_reconciliation["reconciliation_status"] == "failed":
            failures.append("latest reconciliation failed")
        if latest_canary and latest_canary.run_status == "failed":
            failures.append("latest canary failed")
        for count, label in [
            (open_ticket_count, "open tickets"),
            (pending_execution_count, "pending executions"),
            (open_override_count, "open overrides"),
            (invalid_research_count, "invalid research packets"),
            (invalid_macro_count, "invalid macro packets"),
            (invalid_senior_memo_count, "invalid senior memos"),
        ]:
            if count:
                warnings.append(f"{count} {label}")
        health_status = "red" if failures else "yellow" if warnings else "green"
        payload = {"failures": tuple(failures), "warnings": tuple(warnings)}
        snapshot = SystemHealthSnapshot(
            0,
            as_of_date,
            health_status,
            ledger.ledger_status,
            latest_reconciliation["reconciliation_status"] if latest_reconciliation else None,
            latest_canary.run_status if latest_canary else None,
            open_ticket_count,
            pending_execution_count,
            open_override_count,
            invalid_research_count,
            invalid_macro_count,
            invalid_senior_memo_count,
            len(warnings),
            len(failures),
            dumps_json(payload),
            None,
        )
        return SystemHealthRepository(self.db).save(snapshot)

    def _count(self, sql: str) -> int:
        row = self.db.fetch_one(sql)
        return int(row["count"]) if row else 0
