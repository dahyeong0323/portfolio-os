from __future__ import annotations

from datetime import date
from typing import Any

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

    def get(self, decision_id: int) -> dict[str, Any] | None:
        return self.db.fetch_one("SELECT * FROM decision_journal WHERE decision_id = ?", (decision_id,))

    def list_filtered(
        self,
        *,
        decision_type: str | None = None,
        order_ticket_id: int | None = None,
        override_ticket_id: int | None = None,
        risk_validation_id: int | None = None,
        manual_execution_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[object] = []
        if decision_type is not None:
            clauses.append("decision_type = ?")
            params.append(decision_type)
        if order_ticket_id is not None:
            clauses.append("order_ticket_id = ?")
            params.append(order_ticket_id)
        if override_ticket_id is not None:
            clauses.append("override_ticket_id = ?")
            params.append(override_ticket_id)
        if risk_validation_id is not None:
            clauses.append("risk_validation_id = ?")
            params.append(risk_validation_id)
        if manual_execution_id is not None:
            clauses.append("manual_execution_id = ?")
            params.append(manual_execution_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        return self.db.fetch_all(
            f"SELECT * FROM decision_journal {where} ORDER BY decision_id DESC LIMIT ? OFFSET ?",
            tuple(params),
        )

    def latest_for_ticket(self, order_ticket_id: int, decision_type: str) -> dict[str, object] | None:
        return self.db.fetch_one(
            """
            SELECT * FROM decision_journal
            WHERE order_ticket_id = ? AND decision_type = ?
            ORDER BY decision_id DESC
            LIMIT 1
            """,
            (order_ticket_id, decision_type),
        )

    def latest_for_manual_execution(self, manual_execution_id: int) -> dict[str, object] | None:
        return self.db.fetch_one(
            """
            SELECT * FROM decision_journal
            WHERE manual_execution_id = ? AND decision_type = 'manual_execution_logged'
            ORDER BY decision_id DESC
            LIMIT 1
            """,
            (manual_execution_id,),
        )


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

    def get(self, postmortem_task_id: int) -> dict[str, Any] | None:
        return self.db.fetch_one("SELECT * FROM postmortem_tasks WHERE postmortem_task_id = ?", (postmortem_task_id,))

    def latest_for_override(self, override_ticket_id: int) -> dict[str, Any] | None:
        return self.db.fetch_one(
            """
            SELECT * FROM postmortem_tasks
            WHERE override_ticket_id = ?
            ORDER BY postmortem_task_id DESC
            LIMIT 1
            """,
            (override_ticket_id,),
        )

    def list_filtered(
        self,
        *,
        status: str | None = None,
        order_ticket_id: int | None = None,
        override_ticket_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[object] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if order_ticket_id is not None:
            clauses.append("order_ticket_id = ?")
            params.append(order_ticket_id)
        if override_ticket_id is not None:
            clauses.append("override_ticket_id = ?")
            params.append(override_ticket_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        return self.db.fetch_all(
            f"SELECT * FROM postmortem_tasks {where} ORDER BY due_date, postmortem_task_id LIMIT ? OFFSET ?",
            tuple(params),
        )
