from __future__ import annotations

from datetime import date

from portfolio_os.db.connection import Database
from portfolio_os.serialization import dumps_json


class DecisionJournalRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(self, decision_type: str, human_decision: str, reason: str | None = None, order_ticket_id: int | None = None, override_ticket_id: int | None = None, risk_validation_id: int | None = None, manual_execution_id: int | None = None, emotional_state: str | None = None, context: dict[str, object] | None = None) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO decision_journal(decision_type, order_ticket_id, override_ticket_id, risk_validation_id, manual_execution_id,
            human_decision, reason, emotional_state, context_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (decision_type, order_ticket_id, override_ticket_id, risk_validation_id, manual_execution_id, human_decision, reason, emotional_state, dumps_json(context or {})),
        )
        self.db.commit()
        return cursor.lastrowid

    def list(self) -> list[dict[str, object]]:
        return self.db.fetch_all("SELECT * FROM decision_journal ORDER BY decision_id")


class PostmortemTaskRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def schedule(self, due_date: date, order_ticket_id: int | None = None, override_ticket_id: int | None = None, questions: list[str] | None = None) -> int:
        cursor = self.db.execute(
            "INSERT INTO postmortem_tasks(order_ticket_id, override_ticket_id, due_date, status, prompt_questions_json) VALUES (?, ?, ?, 'scheduled', ?)",
            (order_ticket_id, override_ticket_id, due_date.isoformat(), dumps_json(questions or ["What did I expect?", "What happened?", "What should change?"])),
        )
        self.db.commit()
        return cursor.lastrowid
