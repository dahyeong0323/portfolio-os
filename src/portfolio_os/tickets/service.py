from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.intents.repository import TransactionIntentRepository
from portfolio_os.journal.service import DecisionJournalService
from portfolio_os.risk.repositories import RiskValidationRepository
from portfolio_os.tickets.repository import OrderTicketRepository


class OrderTicketService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.tickets = OrderTicketRepository(db)
        self.intents = TransactionIntentRepository(db)
        self.validations = RiskValidationRepository(db)

    def create_ticket_from_validation(self, risk_validation_id: int, expires_at: datetime) -> object:
        result = self.validations.get(risk_validation_id)
        if result.validation_status == "rejected":
            raise ValueError("cannot create order ticket from rejected validation")
        if result.expires_at and result.expires_at < datetime.now(timezone.utc):
            raise ValueError("cannot create order ticket from expired validation")
        intent = self.intents.get(result.intent_id)
        quantity = result.approved_quantity or intent.requested_quantity
        notional = result.approved_notional or intent.requested_notional
        if quantity is None:
            if intent.limit_price is None or notional is None:
                raise ValueError("quantity or notional with limit price is required")
            quantity = notional / intent.limit_price
        if notional is None:
            if intent.limit_price is None:
                raise ValueError("notional or limit price is required")
            notional = abs(quantity * intent.limit_price)
        ticket = self.tickets.create(intent.intent_id, risk_validation_id, intent.account_id, intent.instrument_id, intent.intent_type, quantity, intent.limit_price, notional, intent.currency, expires_at)
        self.intents.update_status(intent.intent_id, "ticket_created")
        return ticket

    def approve_ticket(self, order_ticket_id: int, reason: str | None = None, emotional_state: str | None = None) -> object:
        ticket = self.tickets.get(order_ticket_id)
        if ticket.status != "validated":
            raise ValueError("only validated tickets can be approved")
        if ticket.expires_at < datetime.now(timezone.utc):
            return self.tickets.update_status(order_ticket_id, "expired", "cancelled", "ticket expired")
        updated = self.tickets.update_status(order_ticket_id, "approved", "approved", reason)
        DecisionJournalService(self.db).record_ticket_decision(order_ticket_id, "approved", reason, emotional_state)
        return updated

    def reject_ticket(self, order_ticket_id: int, reason: str, emotional_state: str | None = None) -> object:
        if not reason:
            raise ValueError("rejection reason is required")
        ticket = self.tickets.get(order_ticket_id)
        if ticket.status != "validated":
            raise ValueError("only validated tickets can be rejected")
        updated = self.tickets.update_status(order_ticket_id, "rejected", "rejected", reason)
        DecisionJournalService(self.db).record_ticket_decision(order_ticket_id, "rejected", reason, emotional_state)
        return updated

    def modify_ticket(self, order_ticket_id: int, requested_quantity: Decimal | None, requested_notional: Decimal | None, reason: str):
        ticket = self.tickets.update_status(order_ticket_id, "modified", "modified", reason)
        DecisionJournalService(self.db).record_ticket_decision(order_ticket_id, "modified", reason)
        intent = self.intents.get(ticket.intent_id)
        return self.intents.create(intent.account_id, intent.instrument_id, intent.intent_type, intent.currency, requested_quantity, requested_notional, intent.limit_price, reason)
