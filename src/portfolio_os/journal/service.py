from __future__ import annotations

from portfolio_os.db.connection import Database
from portfolio_os.journal.repository import DecisionJournalRepository


class DecisionJournalService:
    def __init__(self, db: Database) -> None:
        self.repo = DecisionJournalRepository(db)

    def record_ticket_decision(self, order_ticket_id: int, decision: str, reason: str | None, emotional_state: str | None = None) -> int:
        decision_type = {
            "approved": "ticket_approval",
            "rejected": "ticket_rejection",
            "modified": "ticket_modification",
        }.get(decision, "ticket_modification")
        return self.repo.record(decision_type, decision, reason, order_ticket_id=order_ticket_id, emotional_state=emotional_state)

    def record_override_decision(self, override_ticket_id: int, decision: str, reason: str | None, emotional_state: str | None = None) -> int:
        return self.repo.record("override_declared", decision, reason, override_ticket_id=override_ticket_id, emotional_state=emotional_state)

    def record_manual_execution(self, manual_execution_id: int, reason: str | None = None) -> int:
        return self.repo.record("manual_execution_logged", "logged", reason, manual_execution_id=manual_execution_id)
