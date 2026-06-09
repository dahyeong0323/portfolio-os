from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import OverrideTicket
from portfolio_os.validators import date_from_text, datetime_from_text, decimal_from_text, decimal_to_text


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def override_from_row(row: dict[str, Any]) -> OverrideTicket:
    return OverrideTicket(
        override_ticket_id=row["override_ticket_id"],
        override_type=row["override_type"],
        account_id=row["account_id"],
        instrument_id=row["instrument_id"],
        side=row["side"],
        requested_quantity=decimal_from_text(row["requested_quantity"], allow_none=True),
        requested_notional=decimal_from_text(row["requested_notional"], allow_none=True),
        currency=row["currency"],
        ledger_status_at_declaration=row["ledger_status_at_declaration"],
        risk_warning=row["risk_warning"],
        max_suggested_notional=decimal_from_text(row["max_suggested_notional"], allow_none=True),
        human_reason=row["human_reason"],
        human_final_choice=row["human_final_choice"],
        status=row["status"],
        mandatory_reconciliation_deadline=date_from_text(row["mandatory_reconciliation_deadline"]),
        mandatory_postmortem_date=date_from_text(row["mandatory_postmortem_date"]),
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
    )


class OverrideTicketRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, *, override_type: str, account_id: int, instrument_id: int | None, side: str | None, requested_quantity: Decimal | None, requested_notional: Decimal | None, currency: str | None, ledger_status: str, risk_warning: str, human_reason: str, max_suggested_notional: Decimal | None = None, mandatory_reconciliation_deadline: date | None = None, mandatory_postmortem_date: date | None = None) -> OverrideTicket:
        if not human_reason:
            raise ValueError("override requires human reason")
        cursor = self.db.execute(
            """
            INSERT INTO override_tickets(override_type, account_id, instrument_id, side, requested_quantity, requested_notional, currency,
            ledger_status_at_declaration, risk_warning, max_suggested_notional, human_reason, status, mandatory_reconciliation_deadline, mandatory_postmortem_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'risk_warned', ?, ?)
            """,
            (
                override_type,
                account_id,
                instrument_id,
                side,
                decimal_to_text(requested_quantity, allow_none=True),
                decimal_to_text(requested_notional, allow_none=True),
                currency,
                ledger_status,
                risk_warning,
                decimal_to_text(max_suggested_notional, allow_none=True),
                human_reason,
                mandatory_reconciliation_deadline.isoformat() if mandatory_reconciliation_deadline else None,
                mandatory_postmortem_date.isoformat() if mandatory_postmortem_date else None,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, override_ticket_id: int) -> OverrideTicket:
        row = self.db.fetch_one("SELECT * FROM override_tickets WHERE override_ticket_id = ?", (override_ticket_id,))
        if row is None:
            raise ValueError(f"override ticket not found: {override_ticket_id}")
        return override_from_row(row)

    def update_status(self, override_ticket_id: int, status: str, final_choice: str | None = None) -> OverrideTicket:
        self.db.execute(
            "UPDATE override_tickets SET status = ?, human_final_choice = COALESCE(?, human_final_choice), updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE override_ticket_id = ?",
            (status, final_choice, override_ticket_id),
        )
        self.db.commit()
        return self.get(override_ticket_id)

    def list_open(self) -> list[OverrideTicket]:
        return [override_from_row(row) for row in self.db.fetch_all("SELECT * FROM override_tickets WHERE status IN ('declared','risk_warned','human_confirmed') ORDER BY override_ticket_id")]
