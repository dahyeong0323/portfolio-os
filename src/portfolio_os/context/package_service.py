from __future__ import annotations

from datetime import date

from portfolio_os.context.models import ContextPackage
from portfolio_os.context.repositories import ContextPackageRepository
from portfolio_os.db.connection import Database
from portfolio_os.governance.repositories import GovernancePolicyRepository
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.repositories import ReconciliationRepository
from portfolio_os.serialization import dumps_json

ALLOWED_CONTEXT_ITEM_TYPES = {
    "reconciliation",
    "risk_validation",
    "order_ticket",
    "execution",
    "override",
    "research_packet",
    "macro_context",
    "senior_memo",
    "journal",
    "postmortem",
    "system_health",
    "memory",
}

ITEM_TABLE_BY_TYPE = {
    "reconciliation": ("reconciliation_snapshots", "reconciliation_id"),
    "risk_validation": ("risk_validation_results", "risk_validation_id"),
    "order_ticket": ("order_tickets", "order_ticket_id"),
    "execution": ("manual_execution_logs", "manual_execution_id"),
    "override": ("override_tickets", "override_ticket_id"),
    "research_packet": ("research_packets", "research_packet_id"),
    "macro_context": ("macro_context_packets", "macro_context_packet_id"),
    "senior_memo": ("senior_memos", "senior_memo_id"),
    "journal": ("decision_journal", "decision_id"),
    "postmortem": ("postmortem_tasks", "postmortem_task_id"),
    "system_health": ("system_health_snapshots", "system_health_snapshot_id"),
    "memory": ("memory_items", "memory_item_id"),
}


class ContextPackageService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.repo = ContextPackageRepository(db)

    def create_package(self, package_name: str, package_scope: str, as_of_date: date, summary_text: str | None = None, created_by: str = "human") -> ContextPackage:
        ledger = LedgerSnapshotBuilder(self.db).build_snapshot(as_of_date)
        latest_reconciliation = ReconciliationRepository(self.db).get_latest_reconciliation()
        return self.repo.create_package(package_name, package_scope, as_of_date, ledger.ledger_status, latest_reconciliation["reconciliation_id"] if latest_reconciliation else None, summary_text, created_by)

    def add_item(self, context_package_id: int, item_type: str, item_id: int, item_role: str = "context", item_title: str | None = None, item_summary: str | None = None):
        if item_type not in ALLOWED_CONTEXT_ITEM_TYPES:
            raise ValueError(f"context item type is not allowed: {item_type}")
        if item_type == "order_ticket" and item_role != "context":
            raise ValueError("order_ticket items are context only, never instruction")
        if item_type == "execution" and item_role not in {"context", "history"}:
            raise ValueError("execution items are history/context only")
        return self.repo.add_item(context_package_id, item_type, item_id, item_role, item_title, item_summary)

    def validate_package(self, context_package_id: int):
        self.repo.get(context_package_id)
        items = self.repo.list_items(context_package_id)
        failures: list[str] = []
        warnings: list[str] = []
        for item in items:
            status, note = self._validate_item(item.item_type, item.item_id, item.item_role)
            self.repo.update_item_validation(item.context_package_item_id, status, note)
            if status == "invalid":
                failures.append(note or f"invalid {item.item_type}:{item.item_id}")
            elif status == "warning":
                warnings.append(note or f"warning {item.item_type}:{item.item_id}")

        max_items, warning_items = self._budget_limits()
        item_count = len(items)
        if item_count > max_items:
            failures.append(f"context package exceeds MAX_CONTEXT_ITEMS={max_items}")
            budget_status = "failed"
        elif item_count >= warning_items:
            warnings.append(f"context package reached CONTEXT_BUDGET_WARNING_ITEMS={warning_items}")
            budget_status = "warning"
        else:
            budget_status = "ok"
        if failures:
            budget_status = "failed"
        estimated_tokens = self._estimate_tokens(items)
        self.repo.save_budget_record(context_package_id, item_count, max_items, warning_items, estimated_tokens, budget_status, tuple(warnings))
        package_status = "invalid" if failures else "valid"
        return self.repo.update_status(context_package_id, package_status, budget_status)

    def _validate_item(self, item_type: str, item_id: int, item_role: str) -> tuple[str, str | None]:
        if item_type not in ITEM_TABLE_BY_TYPE:
            return "invalid", f"context item type is not allowed: {item_type}"
        table, column = ITEM_TABLE_BY_TYPE[item_type]
        row = self.db.fetch_one(f"SELECT * FROM {table} WHERE {column} = ?", (item_id,))
        if row is None:
            return "invalid", f"{item_type} item not found: {item_id}"
        if item_type == "research_packet" and not (row["packet_status"] == "valid" and row["qa_status"] == "passed"):
            return "invalid", "research_packet must have packet_status='valid' and qa_status='passed'"
        if item_type == "macro_context" and row["packet_status"] != "valid":
            return "invalid", "macro_context must have packet_status='valid'"
        if item_type == "senior_memo" and not (row["memo_status"] == "valid" and row["qa_status"] == "passed"):
            return "invalid", "senior_memo must have memo_status='valid' and qa_status='passed'"
        if item_type == "order_ticket" and item_role != "context":
            return "invalid", "order_ticket can be included only as context, never as instruction"
        if item_type == "execution" and item_role not in {"context", "history"}:
            return "invalid", "execution can be included only as history/context"
        if item_type in {"order_ticket", "execution"}:
            return "warning", f"{item_type} included as context/history only; it is not an instruction"
        return "valid", None

    def _budget_limits(self) -> tuple[int, int]:
        rules = {rule.rule_code: rule for rule in GovernancePolicyRepository(self.db).list_rules()}
        max_items = int(rules.get("MAX_CONTEXT_ITEMS").threshold_value or rules.get("MAX_CONTEXT_ITEMS").rule_value) if "MAX_CONTEXT_ITEMS" in rules else 50
        warning_items = int(rules.get("CONTEXT_BUDGET_WARNING_ITEMS").threshold_value or rules.get("CONTEXT_BUDGET_WARNING_ITEMS").rule_value) if "CONTEXT_BUDGET_WARNING_ITEMS" in rules else 40
        return max_items, warning_items

    def _estimate_tokens(self, items) -> int:
        text = "".join((item.item_title or "") + (item.item_summary or "") for item in items)
        return max(1, (len(text) + 3) // 4) if items else 0

    def package_payload(self, context_package_id: int) -> dict:
        package = self.repo.get(context_package_id)
        items = self.repo.list_items(context_package_id)
        budget = self.repo.latest_budget(context_package_id)
        return {"package": package, "items": items, "budget": budget, "not_order_authority": True}
