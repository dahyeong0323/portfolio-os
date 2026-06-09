from __future__ import annotations

from datetime import date
from typing import Any

from portfolio_os.context.models import ContextBudgetRecord, ContextPackage, ContextPackageItem, DeltaReview, MemoryItem
from portfolio_os.db.connection import Database
from portfolio_os.serialization import dumps_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, require_text


def _bool(value: Any) -> bool:
    return bool(int(value))


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def package_from_row(row: dict[str, Any]) -> ContextPackage:
    return ContextPackage(
        row["context_package_id"],
        row["package_name"],
        row["package_scope"],
        date_from_text(row["as_of_date"]),
        row["package_status"],
        row["ledger_status"],
        row["latest_reconciliation_id"],
        row["summary_text"],
        row["budget_status"],
        row["created_by"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def item_from_row(row: dict[str, Any]) -> ContextPackageItem:
    return ContextPackageItem(row["context_package_item_id"], row["context_package_id"], row["item_type"], row["item_id"], row["item_role"], row["item_title"], row["item_summary"], row["validation_status"], row["validation_note"], _dt(row["created_at"]))


def budget_from_row(row: dict[str, Any]) -> ContextBudgetRecord:
    return ContextBudgetRecord(row["context_budget_record_id"], row["context_package_id"], row["item_count"], row["max_item_count"], row["warning_item_count"], row["estimated_token_count"], row["budget_status"], row["warnings_json"], _dt(row["created_at"]))


def delta_from_row(row: dict[str, Any]) -> DeltaReview:
    return DeltaReview(row["delta_review_id"], row["review_name"], row["previous_context_package_id"], row["current_context_package_id"], row["review_status"], row["added_items_json"], row["removed_items_json"], row["changed_items_json"], row["review_summary"], _dt(row["created_at"]))


def memory_from_row(row: dict[str, Any]) -> MemoryItem:
    return MemoryItem(row["memory_item_id"], row["memory_type"], row["memory_key"], row["memory_text"], row["source_item_type"], row["source_item_id"], row["importance"], _bool(row["is_active"]), _dt(row["created_at"]), _dt(row["updated_at"]))


class ContextPackageRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_package(self, package_name: str, package_scope: str, as_of_date: date, ledger_status: str | None, latest_reconciliation_id: int | None, summary_text: str | None = None, created_by: str = "human") -> ContextPackage:
        require_text(package_name, "package_name")
        cursor = self.db.execute(
            """
            INSERT INTO context_packages(package_name, package_scope, as_of_date, ledger_status, latest_reconciliation_id, summary_text, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (package_name, package_scope, date_to_text(as_of_date), ledger_status, latest_reconciliation_id, summary_text, created_by),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, context_package_id: int) -> ContextPackage:
        row = self.db.fetch_one("SELECT * FROM context_packages WHERE context_package_id = ?", (context_package_id,))
        if row is None:
            raise ValueError(f"context package not found: {context_package_id}")
        return package_from_row(row)

    def update_status(self, context_package_id: int, package_status: str, budget_status: str) -> ContextPackage:
        self.db.execute(
            "UPDATE context_packages SET package_status = ?, budget_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE context_package_id = ?",
            (package_status, budget_status, context_package_id),
        )
        self.db.commit()
        return self.get(context_package_id)

    def add_item(self, context_package_id: int, item_type: str, item_id: int, item_role: str = "context", item_title: str | None = None, item_summary: str | None = None) -> ContextPackageItem:
        cursor = self.db.execute(
            """
            INSERT INTO context_package_items(context_package_id, item_type, item_id, item_role, item_title, item_summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (context_package_id, item_type, item_id, item_role, item_title, item_summary),
        )
        self.db.commit()
        return self.get_item(cursor.lastrowid)

    def get_item(self, context_package_item_id: int) -> ContextPackageItem:
        row = self.db.fetch_one("SELECT * FROM context_package_items WHERE context_package_item_id = ?", (context_package_item_id,))
        if row is None:
            raise ValueError(f"context package item not found: {context_package_item_id}")
        return item_from_row(row)

    def list_items(self, context_package_id: int) -> list[ContextPackageItem]:
        return [item_from_row(row) for row in self.db.fetch_all("SELECT * FROM context_package_items WHERE context_package_id = ? ORDER BY context_package_item_id", (context_package_id,))]

    def update_item_validation(self, context_package_item_id: int, validation_status: str, validation_note: str | None) -> ContextPackageItem:
        self.db.execute(
            "UPDATE context_package_items SET validation_status = ?, validation_note = ? WHERE context_package_item_id = ?",
            (validation_status, validation_note, context_package_item_id),
        )
        self.db.commit()
        return self.get_item(context_package_item_id)

    def save_budget_record(self, context_package_id: int, item_count: int, max_item_count: int, warning_item_count: int, estimated_token_count: int, budget_status: str, warnings: tuple[str, ...]) -> ContextBudgetRecord:
        cursor = self.db.execute(
            """
            INSERT INTO context_budget_records(context_package_id, item_count, max_item_count, warning_item_count,
            estimated_token_count, budget_status, warnings_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (context_package_id, item_count, max_item_count, warning_item_count, estimated_token_count, budget_status, dumps_json(warnings)),
        )
        self.db.commit()
        return self.get_budget_record(cursor.lastrowid)

    def get_budget_record(self, context_budget_record_id: int) -> ContextBudgetRecord:
        row = self.db.fetch_one("SELECT * FROM context_budget_records WHERE context_budget_record_id = ?", (context_budget_record_id,))
        if row is None:
            raise ValueError(f"context budget record not found: {context_budget_record_id}")
        return budget_from_row(row)

    def latest_budget(self, context_package_id: int) -> ContextBudgetRecord | None:
        row = self.db.fetch_one("SELECT * FROM context_budget_records WHERE context_package_id = ? ORDER BY context_budget_record_id DESC LIMIT 1", (context_package_id,))
        return budget_from_row(row) if row else None


class DeltaReviewRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_review(self, review_name: str, previous_context_package_id: int | None, current_context_package_id: int | None, added_items_json: str, removed_items_json: str, changed_items_json: str, review_summary: str | None = None) -> DeltaReview:
        cursor = self.db.execute(
            """
            INSERT INTO delta_reviews(review_name, previous_context_package_id, current_context_package_id, review_status,
            added_items_json, removed_items_json, changed_items_json, review_summary)
            VALUES (?, ?, ?, 'complete', ?, ?, ?, ?)
            """,
            (review_name, previous_context_package_id, current_context_package_id, added_items_json, removed_items_json, changed_items_json, review_summary),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, delta_review_id: int) -> DeltaReview:
        row = self.db.fetch_one("SELECT * FROM delta_reviews WHERE delta_review_id = ?", (delta_review_id,))
        if row is None:
            raise ValueError(f"delta review not found: {delta_review_id}")
        return delta_from_row(row)


class MemoryRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_item(self, memory_type: str, memory_key: str, memory_text: str, source_item_type: str | None = None, source_item_id: int | None = None, importance: str = "medium") -> MemoryItem:
        require_text(memory_key, "memory_key")
        require_text(memory_text, "memory_text")
        cursor = self.db.execute(
            """
            INSERT INTO memory_items(memory_type, memory_key, memory_text, source_item_type, source_item_id, importance)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (memory_type, memory_key, memory_text, source_item_type, source_item_id, importance),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, memory_item_id: int) -> MemoryItem:
        row = self.db.fetch_one("SELECT * FROM memory_items WHERE memory_item_id = ?", (memory_item_id,))
        if row is None:
            raise ValueError(f"memory item not found: {memory_item_id}")
        return memory_from_row(row)

    def list_active(self, memory_type: str | None = None) -> list[MemoryItem]:
        if memory_type:
            rows = self.db.fetch_all("SELECT * FROM memory_items WHERE is_active = 1 AND memory_type = ? ORDER BY memory_item_id", (memory_type,))
        else:
            rows = self.db.fetch_all("SELECT * FROM memory_items WHERE is_active = 1 ORDER BY memory_item_id")
        return [memory_from_row(row) for row in rows]
