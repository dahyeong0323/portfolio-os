from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ContextPackage:
    context_package_id: int
    package_name: str
    package_scope: str
    as_of_date: date
    package_status: str
    ledger_status: str | None
    latest_reconciliation_id: int | None
    summary_text: str | None
    budget_status: str
    created_by: str
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class ContextPackageItem:
    context_package_item_id: int
    context_package_id: int
    item_type: str
    item_id: int
    item_role: str
    item_title: str | None
    item_summary: str | None
    validation_status: str
    validation_note: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class ContextBudgetRecord:
    context_budget_record_id: int
    context_package_id: int
    item_count: int
    max_item_count: int
    warning_item_count: int
    estimated_token_count: int
    budget_status: str
    warnings_json: str
    created_at: datetime | None


@dataclass(frozen=True)
class DeltaReview:
    delta_review_id: int
    review_name: str
    previous_context_package_id: int | None
    current_context_package_id: int | None
    review_status: str
    added_items_json: str
    removed_items_json: str
    changed_items_json: str
    review_summary: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class MemoryItem:
    memory_item_id: int
    memory_type: str
    memory_key: str
    memory_text: str
    source_item_type: str | None
    source_item_id: int | None
    importance: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None
