from __future__ import annotations

from pathlib import Path

from portfolio_os.models import ReconciliationResult
from portfolio_os.serialization import dumps_json


class ReconciliationReportWriter:
    def write_markdown_report(self, result: ReconciliationResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Reconciliation Report",
            "",
            f"- Reconciliation ID: {result.reconciliation_id}",
            f"- As of date: {result.as_of_date.isoformat()}",
            f"- Status: {result.reconciliation_status}",
            f"- Ledger before: {result.ledger_status_before}",
            f"- Ledger after: {result.ledger_status_after}",
            f"- Failure reason: {result.failure_reason or '-'}",
            "",
            "## Differences",
            "",
            f"- Position differences over/within tolerance: {len(result.position_differences)}",
            f"- Cash differences over/within tolerance: {len(result.cash_differences)}",
            f"- Liability differences over/within tolerance: {len(result.liability_differences)}",
            f"- Tax reserve differences over/within tolerance: {len(result.tax_reserve_differences)}",
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, result: ReconciliationResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(result), encoding="utf-8")
        return output_path
