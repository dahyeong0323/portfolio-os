from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.journal.service import DecisionJournalService
from portfolio_os.override.repository import OverrideTicketRepository
from portfolio_os.state import LedgerStateMachine
from portfolio_os.validators import utc_now


class OverrideService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.repo = OverrideTicketRepository(db)

    def declare_override(
        self,
        override_type: str,
        account_id: int,
        instrument_id: int | None,
        side: str | None,
        requested_quantity: Decimal | None,
        requested_notional: Decimal | None,
        currency: str | None,
        human_reason: str,
    ):
        ledger_status = LedgerStateMachine(self.db).get_current_status(account_id)
        now = utc_now().date()
        warning = f"Declared override while ledger_status={ledger_status}. This is not an official risk-validated ticket."
        override = self.repo.create(
            override_type=override_type,
            account_id=account_id,
            instrument_id=instrument_id,
            side=side,
            requested_quantity=requested_quantity,
            requested_notional=requested_notional,
            currency=currency,
            ledger_status=ledger_status,
            risk_warning=warning,
            human_reason=human_reason,
            mandatory_reconciliation_deadline=now + timedelta(days=1),
            mandatory_postmortem_date=now + timedelta(days=7),
        )
        DecisionJournalService(self.db).record_override_decision(override.override_ticket_id, "declared", human_reason)
        return override

    def confirm_override(self, override_ticket_id: int, final_choice: str):
        if final_choice not in {"execute", "cancel", "modify"}:
            raise ValueError("final_choice must be execute, cancel, or modify")
        status = "human_confirmed" if final_choice == "execute" else "cancelled"
        override = self.repo.update_status(override_ticket_id, status, final_choice)
        DecisionJournalService(self.db).record_override_decision(override_ticket_id, final_choice, "override final choice")
        return override
