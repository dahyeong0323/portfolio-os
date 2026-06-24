from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import OrderTicket
from portfolio_os.serialization import dumps_json
from portfolio_os.validators import datetime_from_text, decimal_from_text, decimal_to_text


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


@dataclass(frozen=True)
class OrderTicketEvent:
    event_id: int
    order_ticket_id: int
    event_type: str
    from_status: str | None
    to_status: str
    event_payload_json: str | None
    created_at: datetime | None


def ticket_from_row(row: dict[str, Any]) -> OrderTicket:
    return OrderTicket(
        row["order_ticket_id"],
        row["intent_id"],
        row["risk_validation_id"],
        row["account_id"],
        row["instrument_id"],
        row["side"],
        row["order_type"],
        decimal_from_text(row["ticket_quantity"]),
        decimal_from_text(row["limit_price"], allow_none=True),
        decimal_from_text(row["ticket_notional"]),
        row["currency"],
        row["status"],
        row["human_decision"],
        row["human_decision_reason"],
        _dt(row["approved_at"]),
        _dt(row["rejected_at"]),
        datetime_from_text(row["expires_at"]),
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


class OrderTicketRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, intent_id: int, risk_validation_id: int, account_id: int, instrument_id: int, side: str, ticket_quantity: Decimal, limit_price: Decimal | None, ticket_notional: Decimal, currency: str, expires_at: datetime) -> OrderTicket:
        cursor = self.db.execute(
            """
            INSERT INTO order_tickets(intent_id, risk_validation_id, account_id, instrument_id, side, order_type, ticket_quantity,
            limit_price, ticket_notional, currency, status, expires_at)
            VALUES (?, ?, ?, ?, ?, 'limit', ?, ?, ?, ?, 'validated', ?)
            """,
            (intent_id, risk_validation_id, account_id, instrument_id, side, decimal_to_text(ticket_quantity), decimal_to_text(limit_price, allow_none=True), decimal_to_text(ticket_notional), currency, expires_at.isoformat().replace("+00:00", "Z")),
        )
        self.db.commit()
        ticket = self.get(cursor.lastrowid)
        self.add_event(ticket.order_ticket_id, "created", None, "validated", {"risk_validation_id": risk_validation_id})
        return ticket

    def get(self, order_ticket_id: int) -> OrderTicket:
        row = self.db.fetch_one("SELECT * FROM order_tickets WHERE order_ticket_id = ?", (order_ticket_id,))
        if row is None:
            raise ValueError(f"order ticket not found: {order_ticket_id}")
        return ticket_from_row(row)

    def update_status(self, order_ticket_id: int, status: str, decision: str | None = None, reason: str | None = None) -> OrderTicket:
        previous = self.get(order_ticket_id)
        approved_at = "strftime('%Y-%m-%dT%H:%M:%SZ','now')" if status == "approved" else "approved_at"
        rejected_at = "strftime('%Y-%m-%dT%H:%M:%SZ','now')" if status == "rejected" else "rejected_at"
        self.db.execute(
            f"""
            UPDATE order_tickets SET status = ?, human_decision = COALESCE(?, human_decision),
            human_decision_reason = COALESCE(?, human_decision_reason), approved_at = {approved_at},
            rejected_at = {rejected_at}, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
            WHERE order_ticket_id = ?
            """,
            (status, decision, reason, order_ticket_id),
        )
        self.db.commit()
        self.add_event(order_ticket_id, status if status in {"approved","rejected","modified","expired","cancelled","reconciled","broken"} else "execution_logged", previous.status, status, {"reason": reason})
        return self.get(order_ticket_id)

    def add_event(self, order_ticket_id: int, event_type: str, from_status: str | None, to_status: str, payload: dict[str, object]) -> None:
        self.db.execute(
            "INSERT INTO order_ticket_events(order_ticket_id, event_type, from_status, to_status, event_payload_json) VALUES (?, ?, ?, ?, ?)",
            (order_ticket_id, event_type, from_status, to_status, dumps_json(payload)),
        )
        self.db.commit()

    def list_open(self) -> list[OrderTicket]:
        return [ticket_from_row(row) for row in self.db.fetch_all("SELECT * FROM order_tickets WHERE status IN ('validated','approved') ORDER BY order_ticket_id")]

    def list_all(self) -> list[OrderTicket]:
        return [ticket_from_row(row) for row in self.db.fetch_all("SELECT * FROM order_tickets ORDER BY order_ticket_id")]

    def list_events(self, order_ticket_id: int) -> list[OrderTicketEvent]:
        rows = self.db.fetch_all(
            "SELECT * FROM order_ticket_events WHERE order_ticket_id = ? ORDER BY event_id",
            (order_ticket_id,),
        )
        return [
            OrderTicketEvent(
                event_id=row["event_id"],
                order_ticket_id=row["order_ticket_id"],
                event_type=row["event_type"],
                from_status=row["from_status"],
                to_status=row["to_status"],
                event_payload_json=row["event_payload_json"],
                created_at=_dt(row["created_at"]),
            )
            for row in rows
        ]
