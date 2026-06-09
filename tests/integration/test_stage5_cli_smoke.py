from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from portfolio_os.db import Database, initialize_database

PROTECTED_TABLES = (
    "transactions",
    "cash_balances",
    "reconciliation_snapshots",
    "risk_validation_results",
    "order_tickets",
    "order_ticket_events",
    "manual_execution_logs",
    "override_tickets",
    "decision_journal",
    "postmortem_tasks",
    "research_packets",
    "research_facts",
    "research_missing_data",
    "macro_context_packets",
    "macro_regime_snapshots",
    "macro_metric_snapshots",
    "correlation_snapshots",
    "senior_memo_input_bundles",
    "senior_memos",
    "senior_memo_sections",
    "decision_candidates",
    "no_action_alternatives",
    "opposing_arguments",
    "decision_change_triggers",
    "senior_memo_qa_results",
)


def run_cli(db_path: Path, *args: str) -> str:
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), *args], cwd=os.getcwd(), env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def table_counts(db_path: Path) -> dict[str, int]:
    with Database(db_path) as db:
        return {table: db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"] for table in PROTECTED_TABLES}


def test_stage5_cli_smoke_and_read_only_contract(tmp_path) -> None:
    db_path = tmp_path / "stage5_cli.sqlite3"
    initialize_database(db_path)
    before = table_counts(db_path)

    policy = json.loads(run_cli(db_path, "seed-default-governance-policy", "--activate", "--report-dir", str(tmp_path / "governance_reports")))
    config = json.loads(run_cli(db_path, "capture-configuration-snapshot", "--name", "cli snapshot", "--as-of-date", "2026-05-01"))
    template = json.loads(run_cli(db_path, "register-template", "--name", "cli_context", "--type", "context_package"))
    version = json.loads(run_cli(db_path, "create-template-version", "--template-id", str(template["template_id"]), "--version", "1.0.0", "--body", "Default context template.", "--default"))
    run_cli(db_path, "activate-template-version", "--template-version-id", str(version["template_version_id"]))
    golden = json.loads(run_cli(db_path, "create-golden-test-set", "--name", "cli authority", "--version", "1"))
    run_cli(db_path, "add-golden-test-case", "--golden-test-set-id", str(golden["golden_test_set_id"]), "--name", "safe", "--type", "valid_context_boundary", "--input-text", "This is context only.", "--expected-status", "passed")
    canary = json.loads(run_cli(db_path, "run-canary", "--scope", "system", "--golden-test-set-id", str(golden["golden_test_set_id"]), "--configuration-snapshot-id", str(config["configuration_snapshot_id"])))
    canary_report = json.loads(run_cli(db_path, "export-canary-report", "--canary-run-id", str(canary["canary_run_id"]), "--report-dir", str(tmp_path / "canary_reports")))
    memory = json.loads(run_cli(db_path, "create-memory-item", "--type", "system_note", "--key", "cli_memory", "--text", "Stage 5 CLI memory item."))
    package = json.loads(run_cli(db_path, "create-context-package", "--name", "CLI context", "--scope", "review", "--as-of-date", "2026-05-01"))
    run_cli(db_path, "add-context-item", "--context-package-id", str(package["context_package_id"]), "--item-type", "memory", "--item-id", str(memory["memory_item_id"]))
    validated = json.loads(run_cli(db_path, "validate-context-package", "--context-package-id", str(package["context_package_id"])))
    context_report = json.loads(run_cli(db_path, "export-context-package", "--context-package-id", str(package["context_package_id"]), "--report-dir", str(tmp_path / "context_packages")))
    health = json.loads(run_cli(db_path, "capture-system-health", "--as-of-date", "2026-05-01"))
    health_report = json.loads(run_cli(db_path, "export-system-health-report", "--system-health-snapshot-id", str(health["system_health_snapshot_id"]), "--report-dir", str(tmp_path / "health_reports")))
    source = json.loads(run_cli(db_path, "register-read-only-source", "--name", "CLI export", "--type", "manual_file", "--read-only-confirmed", "--authority-boundary-note", "Read-only local file import audit."))
    import_run = json.loads(run_cli(db_path, "record-read-only-import", "--integration-source-id", str(source["integration_source_id"]), "--scope", "audit", "--status", "recorded", "--rows-seen", "1"))

    assert policy["policy"]["policy_status"] == "active"
    assert canary["run_status"] == "passed"
    assert validated["package_status"] == "valid"
    assert import_run["rows_seen"] == 1
    assert table_counts(db_path) == before
    for report in (canary_report, context_report, health_report):
        assert Path(report["markdown"]).exists()
        assert Path(report["json"]).exists()
