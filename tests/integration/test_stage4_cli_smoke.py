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
    "research_packets",
    "research_facts",
    "research_missing_data",
    "macro_context_packets",
    "macro_regime_snapshots",
    "macro_metric_snapshots",
    "correlation_snapshots",
)


def run_cli(db_path: Path, *args: str) -> str:
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), *args], cwd=os.getcwd(), env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def table_counts(db_path: Path) -> dict[str, int]:
    with Database(db_path) as db:
        return {table: db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"] for table in PROTECTED_TABLES}


def seed_valid_stage3_cli(db_path: Path) -> tuple[int, int]:
    initialize_database(db_path)
    instrument = json.loads(run_cli(db_path, "add-instrument", "--symbol", "S4CLI", "--name", "Stage4 CLI", "--type", "stock", "--currency", "USD", "--exchange", "SAMPLE"))
    source = json.loads(run_cli(db_path, "add-research-source", "--type", "manual_note", "--title", "Manual source", "--local-path", "notes/s4cli.md"))
    packet = json.loads(run_cli(db_path, "create-research-packet", "--instrument-id", str(instrument["instrument_id"]), "--packet-version", "v1", "--as-of-date", "2026-03-01", "--summary-text", "Facts were collected."))
    packet_id = str(packet["research_packet_id"])
    source_id = str(source["source_id"])
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "bull", "--thesis-relation", "supporting", "--fact-type", "financial", "--text", "Revenue increased.")
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "bear", "--thesis-relation", "challenging", "--fact-type", "competition", "--text", "Competition increased.")
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "neutral", "--thesis-relation", "neutral", "--fact-type", "business", "--text", "The company reported results.")
    run_cli(db_path, "add-missing-data", "--research-packet-id", packet_id, "--question", "Retention data is unknown.")
    run_cli(db_path, "run-research-qa", "--research-packet-id", packet_id)
    macro = json.loads(run_cli(db_path, "create-macro-context", "--as-of-date", "2026-03-01", "--summary-text", "Macro context was reviewed."))
    validated = json.loads(run_cli(db_path, "validate-macro-context", "--macro-context-packet-id", str(macro["macro_context_packet_id"])))
    return int(packet_id), int(validated["macro_context_packet_id"])


def test_stage4_cli_smoke_and_read_only_contract(tmp_path) -> None:
    db_path = tmp_path / "stage4_cli.sqlite3"
    research_id, macro_id = seed_valid_stage3_cli(db_path)
    before = table_counts(db_path)

    bundle = json.loads(run_cli(db_path, "build-senior-input-bundle", "--as-of-date", "2026-03-01", "--research-packet-id", str(research_id), "--macro-context-packet-id", str(macro_id)))
    memo = json.loads(run_cli(db_path, "create-senior-memo", "--input-bundle-id", str(bundle["input_bundle_id"]), "--title", "Stage 4 CLI memo", "--scope", "asset", "--executive-summary", "Executive summary reviewed."))
    memo_id = str(memo["senior_memo_id"])
    for section_type in (
        "portfolio_diagnosis",
        "macro_interpretation",
        "cash_liquidity",
        "asset_thesis_status",
        "risk_context",
        "execution_context",
        "no_action_case",
        "opposing_argument",
        "change_triggers",
        "required_risk_validation",
    ):
        run_cli(db_path, "add-senior-section", "--senior-memo-id", memo_id, "--section-type", section_type, "--title", section_type, "--text", f"{section_type} reviewed.")
    candidate = json.loads(run_cli(db_path, "add-decision-candidate", "--senior-memo-id", memo_id, "--candidate-type", "create_intent_candidate", "--text", "Candidate for later upstream flow.", "--rationale", "Candidate only."))
    run_cli(db_path, "add-no-action-alternative", "--senior-memo-id", memo_id, "--text", "No action.", "--why-reasonable", "No-action remains reasonable.")
    run_cli(db_path, "add-opposing-argument", "--senior-memo-id", memo_id, "--text", "The opposing argument is uncertainty.")
    run_cli(db_path, "add-decision-change-trigger", "--senior-memo-id", memo_id, "--text", "Ledger status changes.", "--type", "ledger")
    qa = json.loads(run_cli(db_path, "run-senior-memo-qa", "--senior-memo-id", memo_id))
    report = json.loads(run_cli(db_path, "export-senior-memo-report", "--senior-memo-id", memo_id, "--report-dir", str(tmp_path / "senior_memos")))

    assert qa["qa_status"] == "passed"
    assert candidate["candidate_status"] == "blocked_pending_reconciliation"
    assert candidate["required_next_step"] == "reconciliation_required"
    text = Path(report["markdown"]).read_text(encoding="utf-8")
    assert "Stage 2 risk validation still required: yes" in text
    assert "Reconciliation required first: yes" in text
    assert table_counts(db_path) == before
    assert Path(report["json"]).exists()
