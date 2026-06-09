from __future__ import annotations

from pathlib import Path

from portfolio_os.context.package_service import ContextPackageService
from portfolio_os.context.repositories import ContextPackageRepository
from portfolio_os.db.connection import Database
from portfolio_os.serialization import dumps_json


class ContextPackageReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, context_package_id: int) -> dict:
        return ContextPackageService(self.db).package_payload(context_package_id)

    def write_markdown_report(self, context_package_id: int, output_path: Path) -> Path:
        payload = self._payload(context_package_id)
        package = payload["package"]
        items = payload["items"]
        budget = payload["budget"]
        lines = [
            f"# Context Package {package.context_package_id}",
            "",
            "This context package is not order authority.",
            "It cannot create, approve, size, validate, or execute trades.",
            "Order tickets are included only as context. Executions are included only as history/context.",
            "",
            f"- Name: {package.package_name}",
            f"- Scope: {package.package_scope}",
            f"- Status: {package.package_status}",
            f"- Budget status: {package.budget_status}",
            f"- Ledger status: {package.ledger_status}",
            "",
            "## Items",
        ]
        if not items:
            lines.append("- none")
        for item in items:
            lines.append(f"- {item.item_type}:{item.item_id} ({item.item_role}) - {item.validation_status}")
            if item.validation_note:
                lines.append(f"  - Note: {item.validation_note}")
        lines.extend(["", "## Budget"])
        if budget:
            lines.append(f"- Item count: {budget.item_count}/{budget.max_item_count}")
            lines.append(f"- Warning threshold: {budget.warning_item_count}")
            lines.append(f"- Estimated tokens: {budget.estimated_token_count}")
        else:
            lines.append("- not_checked")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, context_package_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(context_package_id)), encoding="utf-8")
        return output_path


def latest_context_package_id(db: Database) -> int | None:
    row = db.fetch_one("SELECT context_package_id FROM context_packages ORDER BY context_package_id DESC LIMIT 1")
    return row["context_package_id"] if row else None
