from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date

from portfolio_os.db import Database, initialize_database
from portfolio_os.models import CashBalance
from portfolio_os.repositories import AccountRepository, CashBalanceRepository, InstrumentRepository


PROTECTED_TABLES = (
    "transactions",
    "cash_balances",
    "risk_validation_results",
    "order_tickets",
    "manual_execution_logs",
    "override_tickets",
    "decision_journal",
)


def run_cli(db_path, *args):
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), *args], cwd=os.getcwd(), env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def protected_counts(db_path) -> dict[str, int]:
    with Database(db_path) as db:
        return {table: db.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")["count"] for table in PROTECTED_TABLES}


def seed_stage1_rows(db_path) -> int:
    initialize_database(db_path)
    with Database(db_path) as db:
        account = AccountRepository(db).create_account("Brokerage", "Test Bank", "securities", "USD")
        instrument = InstrumentRepository(db).create_instrument("NFLX", "NFLX Inc.", "stock", "USD", exchange="NASDAQ")
        CashBalanceRepository(db).record_cash_balance(CashBalance(0, account.account_id, date(2026, 2, 1), "USD", "10000", "manual", None, False, None))
        return instrument.instrument_id


def test_stage3_cli_research_and_macro_smoke_preserves_stage1_stage2_tables(tmp_path) -> None:
    db_path = tmp_path / "stage3_cli.sqlite3"
    instrument_id = seed_stage1_rows(db_path)
    before = protected_counts(db_path)

    source = json.loads(run_cli(db_path, "add-research-source", "--type", "manual_note", "--title", "Manual source", "--local-path", "notes/manual.md"))
    packet = json.loads(run_cli(db_path, "create-research-packet", "--instrument-id", str(instrument_id), "--packet-version", "v1", "--as-of-date", "2026-02-01", "--summary-text", "Facts were collected from listed sources."))
    packet_id = str(packet["research_packet_id"])
    source_id = str(source["source_id"])
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "bull", "--thesis-relation", "supporting", "--fact-type", "financial", "--text", "Revenue increased.")
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "bear", "--thesis-relation", "challenging", "--fact-type", "competition", "--text", "Competition increased.")
    run_cli(db_path, "add-research-fact", "--research-packet-id", packet_id, "--source-id", source_id, "--category", "neutral", "--thesis-relation", "neutral", "--fact-type", "business", "--text", "The company reported results.")
    run_cli(db_path, "add-missing-data", "--research-packet-id", packet_id, "--question", "Retention data is unknown.")
    qa = json.loads(run_cli(db_path, "run-research-qa", "--research-packet-id", packet_id))
    assert qa["qa_status"] == "passed"
    research_report = json.loads(run_cli(db_path, "export-research-report", "--research-packet-id", packet_id, "--report-dir", str(tmp_path / "research_reports")))

    context = json.loads(run_cli(db_path, "build-portfolio-context", "--as-of-date", "2026-02-01"))
    metric = json.loads(run_cli(db_path, "record-macro-metric", "--metric-date", "2026-02-01", "--metric-code", "NASDAQ_DRAWDOWN", "--metric-value", "-0.20", "--metric-unit", "ratio"))
    correlation = json.loads(run_cli(db_path, "record-correlation", "--as-of-date", "2026-02-01", "--left-symbol", "PORTFOLIO", "--right-symbol", "QQQ", "--metric-type", "correlation", "--window-days", "30", "--value", "0.90"))
    regime = json.loads(run_cli(db_path, "classify-macro-regime", "--as-of-date", "2026-02-01"))
    macro = json.loads(
        run_cli(
            db_path,
            "create-macro-context",
            "--as-of-date",
            "2026-02-01",
            "--portfolio-context-id",
            str(context["portfolio_context_id"]),
            "--macro-regime-id",
            str(regime["macro_regime_id"]),
            "--summary-text",
            "Macro indicators were elevated and are context only.",
            "--risk-on-exposure",
            "high",
            "--correlation-stress",
            "elevated",
            "--metric-ref",
            str(metric["macro_metric_id"]),
            "--correlation-ref",
            str(correlation["correlation_id"]),
        )
    )
    validated = json.loads(run_cli(db_path, "validate-macro-context", "--macro-context-packet-id", str(macro["macro_context_packet_id"])))
    assert validated["packet_status"] == "valid"
    macro_report = json.loads(run_cli(db_path, "export-macro-context-report", "--macro-context-packet-id", str(macro["macro_context_packet_id"]), "--report-dir", str(tmp_path / "macro_reports")))

    after = protected_counts(db_path)
    assert after == before
    assert os.path.exists(research_report["markdown"])
    assert os.path.exists(research_report["json"])
    assert os.path.exists(macro_report["markdown"])
    assert os.path.exists(macro_report["json"])
