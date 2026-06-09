from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.models import LedgerSnapshot
from portfolio_os.risk.engine import RiskEngine


class ValuationService:
    def __init__(self, db: Database) -> None:
        self.engine = RiskEngine(db)

    def gross_portfolio_value(self, snapshot: LedgerSnapshot, base_currency: str, as_of_date: date) -> Decimal:
        return self.engine._gross_portfolio_value(snapshot, base_currency, as_of_date)
