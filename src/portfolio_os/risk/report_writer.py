from __future__ import annotations

from pathlib import Path

from portfolio_os.risk.models import RiskValidationResult
from portfolio_os.serialization import dumps_json


class RiskReportWriter:
    def write_markdown_report(self, result: RiskValidationResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Risk Validation Report",
            "",
            f"- Risk validation ID: {result.risk_validation_id}",
            f"- Intent ID: {result.intent_id}",
            f"- Ledger status: {result.ledger_status_at_validation}",
            f"- Validation status: {result.validation_status}",
            f"- Action class: {result.action_class}",
            f"- Currency: {result.currency}",
            f"- Approved quantity: {result.approved_quantity}",
            f"- Approved notional: {result.approved_notional}",
            f"- Failure reasons: {', '.join(result.failure_reasons) if result.failure_reasons else '-'}",
            f"- Warnings: {', '.join(result.warnings) if result.warnings else '-'}",
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, result: RiskValidationResult, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(result), encoding="utf-8")
        return output_path
