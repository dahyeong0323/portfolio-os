from __future__ import annotations

from portfolio_os.context.repositories import MemoryRepository
from portfolio_os.db.connection import Database


class MemoryService:
    def __init__(self, db: Database) -> None:
        self.repo = MemoryRepository(db)

    def create_memory_item(self, memory_type: str, memory_key: str, memory_text: str, source_item_type: str | None = None, source_item_id: int | None = None, importance: str = "medium"):
        return self.repo.create_item(memory_type, memory_key, memory_text, source_item_type, source_item_id, importance)

    def list_memory_items(self, memory_type: str | None = None):
        return self.repo.list_active(memory_type)
