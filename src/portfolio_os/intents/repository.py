from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from portfolio_os.db.connection import Database
from portfolio_os.risk.models import TransactionIntent
from portfolio_os.validators import date_from_text, datetime_from_text, decimal_from_text, decimal_to_text


def _dt(value: str | None):
    return datetime_from_text(value) if value else None


def intent_from_row(row: dict[str, Any]) -> TransactionIntent:
    return TransactionIntent(
        intent_id=row["intent_id"],
        account_id=row["account_id"],
        instrument_id=row["instrument_id"],
        intent_type=row["intent_type"],
        intent_source=row["intent_source"],
        requested_quantity=decimal_from_text(row["requested_quantity"], allow_none=True),
        requested_notional=decimal_from_text(row["requested_notional"], allow_none=True),
        limit_price=decimal_from_text(row["limit_price"], allow_none=True),
        currency=row["currency"],
        order_type=row["order_type"],
        rationale=row["rationale"],
        status=row["status"],
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
        expires_at=_dt(row["expires_at"]),
    )


class TransactionIntentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(
        self,
        account_id: int,
        instrument_id: int,
        intent_type: str,
        currency: str,
        requested_quantity: Decimal | None = None,
        requested_notional: Decimal | None = None,
        limit_price: Decimal | None = None,
        rationale: str | None = None,
        intent_source: str = "manual",
        expires_at: datetime | None = None,
    ) -> TransactionIntent:
        if requested_quantity is None and requested_notional is None:
            raise ValueError("requested_quantity or requested_notional is required")
        if requested_quantity is not None and requested_quantity < 0:
            raise ValueError("requested_quantity cannot be negative")
        if requested_notional is not None and requested_notional < 0:
            raise ValueError("requested_notional cannot be negative")
        cursor = self.db.execute(
            """
            INSERT INTO transaction_intents(account_id, instrument_id, intent_type, intent_source, requested_quantity,
            requested_notional, limit_price, currency, order_type, rationale, status, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'limit', ?, 'drafted', ?)
            """,
            (
                account_id,
                instrument_id,
                intent_type,
                intent_source,
                decimal_to_text(requested_quantity, allow_none=True),
                decimal_to_text(requested_notional, allow_none=True),
                decimal_to_text(limit_price, allow_none=True),
                currency,
                rationale,
                expires_at.isoformat().replace("+00:00", "Z") if expires_at else None,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, intent_id: int) -> TransactionIntent:
        row = self.db.fetch_one("SELECT * FROM transaction_intents WHERE intent_id = ?", (intent_id,))
        if row is None:
            raise ValueError(f"intent not found: {intent_id}")
        return intent_from_row(row)

    def update_status(self, intent_id: int, status: str) -> TransactionIntent:
        self.db.execute(
            "UPDATE transaction_intents SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE intent_id = ?",
            (status, intent_id),
        )
        self.db.commit()
        return self.get(intent_id)


class _Noop:
    pass
