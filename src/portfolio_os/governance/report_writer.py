from __future__ import annotations

from pathlib import Path

from portfolio_os.db.connection import Database
from portfolio_os.governance.repositories import (
    CanaryRepository,
    GovernancePolicyRepository,
    SystemHealthRepository,
)
from portfolio_os.serialization import dumps_json


class GovernanceReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def write_policy_report(self, governance_policy_id: int, output_path: Path) -> Path:
        repo = GovernancePolicyRepository(self.db)
        policy = repo.get_policy(governance_policy_id)
        rules = repo.list_rules(governance_policy_id)
        lines = [
            f"# Governance Policy {policy.governance_policy_id}",
            "",
            "This governance policy does not grant trading authority.",
            "It cannot create order tickets, risk validations, approvals, or executions.",
            "",
            f"- Name: {policy.policy_name}",
            f"- Version: {policy.version}",
            f"- Status: {policy.policy_status}",
            f"- Canary required before activation: {'yes' if policy.canary_required_before_activation else 'no'}",
            "",
            "## Rules",
        ]
        for rule in rules:
            lines.append(f"- {rule.rule_code}: {rule.rule_value} ({rule.severity})")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_policy_json(self, governance_policy_id: int, output_path: Path) -> Path:
        repo = GovernancePolicyRepository(self.db)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json({"policy": repo.get_policy(governance_policy_id), "rules": repo.list_rules(governance_policy_id)}), encoding="utf-8")
        return output_path


class CanaryReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, canary_run_id: int) -> dict:
        repo = CanaryRepository(self.db)
        return {"run": repo.get_run(canary_run_id), "results": repo.list_results(canary_run_id), "not_order_authority": True}

    def write_markdown_report(self, canary_run_id: int, output_path: Path) -> Path:
        payload = self._payload(canary_run_id)
        run = payload["run"]
        results = payload["results"]
        lines = [
            f"# Canary Run {run.canary_run_id}",
            "",
            "This canary is a governance and authority-boundary check only.",
            "It does not create orders, risk validations, approvals, or executions.",
            "",
            f"- Scope: {run.run_scope}",
            f"- Status: {run.run_status}",
            f"- Passed: {run.passed_count}",
            f"- Failed: {run.failed_count}",
            f"- Warnings: {run.warning_count}",
            "",
            "## Results",
        ]
        for result in results:
            lines.append(f"- {result.check_code}: {result.result_status} - {result.result_summary}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, canary_run_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(canary_run_id)), encoding="utf-8")
        return output_path


class SystemHealthReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, system_health_snapshot_id: int) -> dict:
        return {"health": SystemHealthRepository(self.db).get(system_health_snapshot_id), "not_order_authority": True}

    def write_markdown_report(self, system_health_snapshot_id: int, output_path: Path) -> Path:
        health = self._payload(system_health_snapshot_id)["health"]
        lines = [
            f"# System Health Snapshot {health.system_health_snapshot_id}",
            "",
            "This health report is operational context only and does not authorize trading.",
            "",
            f"- As of date: {health.as_of_date}",
            f"- Health status: {health.health_status}",
            f"- Ledger status: {health.ledger_status}",
            f"- Latest reconciliation status: {health.latest_reconciliation_status or 'none'}",
            f"- Latest canary status: {health.latest_canary_status or 'none'}",
            f"- Warnings: {health.warning_count}",
            f"- Failures: {health.failure_count}",
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, system_health_snapshot_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(system_health_snapshot_id)), encoding="utf-8")
        return output_path
