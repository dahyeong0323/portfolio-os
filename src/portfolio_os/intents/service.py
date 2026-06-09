from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.intents.repository import TransactionIntentRepository
from portfolio_os.risk.models import TransactionIntent


class TransactionIntentService:
    def __init__(self, db: Database) -> None:
        self.repo = TransactionIntentRepository(db)

    def create_intent(
        self,
        account_id: int,
        instrument_id: int,
        intent_type: str,
        currency: str,
        requested_quantity: Decimal | None = None,
        requested_notional: Decimal | None = None,
        limit_price: Decimal | None = None,
        rationale: str | None = None,
        expires_at: datetime | None = None,
    ) -> TransactionIntent:
        return self.repo.create(account_id, instrument_id, intent_type, currency, requested_quantity, requested_notional, limit_price, rationale, "manual", expires_at)
