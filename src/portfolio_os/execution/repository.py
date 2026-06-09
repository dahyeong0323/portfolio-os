from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import ManualExecutionLog
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, decimal_from_text, decimal_to_text


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def execution_from_row(row: dict[str, Any]) -> ManualExecutionLog:
    return ManualExecutionLog(
        manual_execution_id=row["manual_execution_id"],
        order_ticket_id=row["order_ticket_id"],
        override_ticket_id=row["override_ticket_id"],
        created_transaction_id=row["created_transaction_id"],
        account_id=row["account_id"],
        instrument_id=row["instrument_id"],
        side=row["side"],
        executed_quantity=decimal_from_text(row["executed_quantity"]),
        executed_price=decimal_from_text(row["executed_price"]),
        gross_amount=decimal_from_text(row["gross_amount"]),
        fee_amount=decimal_from_text(row["fee_amount"]),
        tax_amount=decimal_from_text(row["tax_amount"]),
        net_cash_amount=decimal_from_text(row["net_cash_amount"]),
        currency=row["currency"],
        executed_at=datetime_from_text(row["executed_at"]),
        broker_execution_ref=row["broker_execution_ref"],
        execution_status=row["execution_status"],
        reconciliation_deadline=date_from_text(row["reconciliation_deadline"]),
        reconciled_at=_dt(row["reconciled_at"]),
        reconciliation_id=row["reconciliation_id"],
        notes=row["notes"],
    )


class ManualExecutionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, *, order_ticket_id: int | None, override_ticket_id: int | None, account_id: int, instrument_id: int, side: str, executed_quantity: Decimal, executed_price: Decimal, gross_amount: Decimal, fee_amount: Decimal, tax_amount: Decimal, net_cash_amount: Decimal, currency: str, executed_at: datetime, broker_execution_ref: str | None = None, reconciliation_deadline: date | None = None, notes: str | None = None) -> ManualExecutionLog:
        cursor = self.db.execute(
            """
            INSERT INTO manual_execution_logs(order_ticket_id, override_ticket_id, account_id, instrument_id, side,
            executed_quantity, executed_price, gross_amount, fee_amount, tax_amount, net_cash_amount, currency,
            executed_at, broker_execution_ref, execution_status, reconciliation_deadline, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'logged', ?, ?)
            """,
            (
                order_ticket_id,
                override_ticket_id,
                account_id,
                instrument_id,
                side,
                decimal_to_text(executed_quantity),
                decimal_to_text(executed_price),
                decimal_to_text(gross_amount),
                decimal_to_text(fee_amount),
                decimal_to_text(tax_amount),
                decimal_to_text(net_cash_amount),
                currency,
                executed_at.isoformat().replace("+00:00", "Z"),
                broker_execution_ref,
                date_to_text(reconciliation_deadline) if reconciliation_deadline else None,
                notes,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, manual_execution_id: int) -> ManualExecutionLog:
        row = self.db.fetch_one("SELECT * FROM manual_execution_logs WHERE manual_execution_id = ?", (manual_execution_id,))
        if row is None:
            raise ValueError(f"manual execution not found: {manual_execution_id}")
        return execution_from_row(row)

    def update_transaction(self, manual_execution_id: int, transaction_id: int, status: str = "pending_reconciliation") -> ManualExecutionLog:
        self.db.execute(
            "UPDATE manual_execution_logs SET created_transaction_id = ?, execution_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE manual_execution_id = ?",
            (transaction_id, status, manual_execution_id),
        )
        self.db.commit()
        return self.get(manual_execution_id)

    def mark_reconciled(self, manual_execution_id: int, reconciliation_id: int) -> ManualExecutionLog:
        self.db.execute(
            """
            UPDATE manual_execution_logs SET execution_status = 'reconciled', reconciliation_id = ?,
            reconciled_at = strftime('%Y-%m-%dT%H:%M:%SZ','now'), updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
            WHERE manual_execution_id = ?
            """,
            (reconciliation_id, manual_execution_id),
        )
        self.db.commit()
        return self.get(manual_execution_id)

    def mark_failed(self, manual_execution_id: int, reconciliation_id: int) -> ManualExecutionLog:
        self.db.execute(
            "UPDATE manual_execution_logs SET execution_status = 'reconciliation_failed', reconciliation_id = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE manual_execution_id = ?",
            (reconciliation_id, manual_execution_id),
        )
        self.db.commit()
        return self.get(manual_execution_id)

    def list_pending(self) -> list[ManualExecutionLog]:
        return [execution_from_row(row) for row in self.db.fetch_all("SELECT * FROM manual_execution_logs WHERE execution_status = 'pending_reconciliation' ORDER BY manual_execution_id")]
