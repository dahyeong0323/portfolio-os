from __future__ import annotations

from datetime import date

from portfolio_os.db.connection import Database
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.macro.repositories import PortfolioContextRepository
from portfolio_os.repositories import InstrumentRepository, ReconciliationRepository
from portfolio_os.serialization import dumps_json


class PortfolioContextBuilder:
    def __init__(self, db: Database) -> None:
        self.db = db

    def build_context_snapshot(self, as_of_date: date):
        ledger = LedgerSnapshotBuilder(self.db).build_snapshot(as_of_date)
        latest_reconciliation = ReconciliationRepository(self.db).get_latest_reconciliation()
        open_ticket_count = self.db.fetch_one("SELECT COUNT(*) AS count FROM order_tickets WHERE status IN ('validated','approved')")["count"]
        pending_execution_count = self.db.fetch_one("SELECT COUNT(*) AS count FROM manual_execution_logs WHERE execution_status IN ('logged','transaction_created','pending_reconciliation')")["count"]
        open_override_count = self.db.fetch_one("SELECT COUNT(*) AS count FROM override_tickets WHERE status IN ('declared','risk_warned','human_confirmed')")["count"]
        active_instrument_count = len(InstrumentRepository(self.db).list_active_instruments())
        context_json = dumps_json(
            {
                "note": "read-only context cache; not ledger truth",
                "position_count": len(ledger.positions),
                "cash_count": len(ledger.cash),
                "liability_count": len(ledger.liabilities),
                "tax_reserve_count": len(ledger.tax_reserves),
                "open_ticket_count": open_ticket_count,
                "pending_execution_count": pending_execution_count,
                "open_override_count": open_override_count,
            }
        )
        return PortfolioContextRepository(self.db).create_context_snapshot(
            as_of_date=as_of_date,
            ledger_status=ledger.ledger_status,
            latest_reconciliation_id=latest_reconciliation["reconciliation_id"] if latest_reconciliation else None,
            open_ticket_count=open_ticket_count,
            pending_execution_count=pending_execution_count,
            open_override_count=open_override_count,
            active_instrument_count=active_instrument_count,
            context_json=context_json,
        )
