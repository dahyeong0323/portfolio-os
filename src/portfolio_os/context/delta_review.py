from __future__ import annotations

from portfolio_os.context.repositories import ContextPackageRepository, DeltaReviewRepository
from portfolio_os.db.connection import Database
from portfolio_os.serialization import dumps_json


class DeltaReviewService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_delta_review(self, review_name: str, previous_context_package_id: int | None, current_context_package_id: int | None, review_summary: str | None = None):
        package_repo = ContextPackageRepository(self.db)
        previous_items = set()
        current_items = set()
        if previous_context_package_id is not None:
            previous_items = {(item.item_type, item.item_id) for item in package_repo.list_items(previous_context_package_id)}
        if current_context_package_id is not None:
            current_items = {(item.item_type, item.item_id) for item in package_repo.list_items(current_context_package_id)}
        added = tuple({"item_type": item_type, "item_id": item_id} for item_type, item_id in sorted(current_items - previous_items))
        removed = tuple({"item_type": item_type, "item_id": item_id} for item_type, item_id in sorted(previous_items - current_items))
        changed = ()
        return DeltaReviewRepository(self.db).create_review(review_name, previous_context_package_id, current_context_package_id, dumps_json(added), dumps_json(removed), dumps_json(changed), review_summary)
