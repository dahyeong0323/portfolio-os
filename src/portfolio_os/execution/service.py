from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.execution.repository import ManualExecutionRepository
from portfolio_os.journal.service import DecisionJournalService
from portfolio_os.models import Transaction
from portfolio_os.override.repository import OverrideTicketRepository
from portfolio_os.repositories import ReconciliationRepository, TransactionRepository
from portfolio_os.tickets.repository import OrderTicketRepository


class ManualExecutionService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.executions = ManualExecutionRepository(db)

    def log_execution_for_ticket(
        self,
        order_ticket_id: int,
        executed_quantity: Decimal,
        executed_price: Decimal,
        fee_amount: Decimal,
        tax_amount: Decimal,
        executed_at: datetime,
        broker_execution_ref: str | None = None,
    ):
        ticket = OrderTicketRepository(self.db).get(order_ticket_id)
        if ticket.status != "approved":
            raise ValueError("manual execution requires approved ticket")
        gross = abs(executed_quantity * executed_price)
        net = -(gross + fee_amount + tax_amount) if ticket.side == "buy" else gross - fee_amount - tax_amount
        execution = self.executions.create(
            order_ticket_id=order_ticket_id,
            override_ticket_id=None,
            account_id=ticket.account_id,
            instrument_id=ticket.instrument_id,
            side=ticket.side,
            executed_quantity=abs(executed_quantity),
            executed_price=executed_price,
            gross_amount=gross,
            fee_amount=fee_amount,
            tax_amount=tax_amount,
            net_cash_amount=net,
            currency=ticket.currency,
            executed_at=executed_at,
            broker_execution_ref=broker_execution_ref,
        )
        return self.create_provisional_transaction(execution.manual_execution_id)

    def log_execution_for_override(
        self,
        override_ticket,
        executed_quantity: Decimal,
        executed_price: Decimal,
        fee_amount: Decimal,
        tax_amount: Decimal,
        executed_at: datetime,
        broker_execution_ref: str | None = None,
    ):
        if override_ticket.status != "human_confirmed":
            raise ValueError("override execution requires human-confirmed override")
        if override_ticket.instrument_id is None or override_ticket.side is None or override_ticket.currency is None:
            raise ValueError("override execution requires instrument, side, and currency")
        gross = abs(executed_quantity * executed_price)
        net = -(gross + fee_amount + tax_amount) if override_ticket.side == "buy" else gross - fee_amount - tax_amount
        execution = self.executions.create(
            order_ticket_id=None,
            override_ticket_id=override_ticket.override_ticket_id,
            account_id=override_ticket.account_id,
            instrument_id=override_ticket.instrument_id,
            side=override_ticket.side,
            executed_quantity=abs(executed_quantity),
            executed_price=executed_price,
            gross_amount=gross,
            fee_amount=fee_amount,
            tax_amount=tax_amount,
            net_cash_amount=net,
            currency=override_ticket.currency,
            executed_at=executed_at,
            broker_execution_ref=broker_execution_ref,
        )
        return self.create_provisional_transaction(execution.manual_execution_id)

    def create_provisional_transaction(self, execution_id: int):
        execution = self.executions.get(execution_id)
        quantity = execution.executed_quantity if execution.side == "buy" else -execution.executed_quantity
        tx = Transaction(
            transaction_id=0,
            account_id=execution.account_id,
            instrument_id=execution.instrument_id,
            transaction_type=execution.side,
            trade_date=execution.executed_at.date(),
            settlement_date=None,
            currency=execution.currency,
            quantity=quantity,
            price=execution.executed_price,
            gross_amount=execution.gross_amount,
            fee_amount=execution.fee_amount,
            tax_amount=execution.tax_amount,
            net_cash_amount=execution.net_cash_amount,
            fx_rate_to_base=None,
            source="manual",
            external_ref=execution.broker_execution_ref,
            description=f"manual_execution_id={execution.manual_execution_id}",
            is_confirmed=False,
            is_voided=False,
            void_reason=None,
        )
        created = TransactionRepository(self.db).record_transaction(tx)
        updated = self.executions.update_transaction(execution.manual_execution_id, created.transaction_id)
        if updated.order_ticket_id is not None:
            OrderTicketRepository(self.db).update_status(updated.order_ticket_id, "executed_provisional", "approved", "manual execution logged")
        if updated.override_ticket_id is not None:
            OverrideTicketRepository(self.db).update_status(updated.override_ticket_id, "executed_provisional")
        DecisionJournalService(self.db).record_manual_execution(updated.manual_execution_id, "manual execution logged and provisional transaction created")
        return updated

    def mark_reconciled_after_passed_reconciliation(self, reconciliation_id: int) -> int:
        reconciliation = ReconciliationRepository(self.db).get_latest_reconciliation()
        if reconciliation is None or reconciliation["reconciliation_id"] != reconciliation_id or reconciliation["reconciliation_status"] != "passed":
            return 0
        count = 0
        tx_repo = TransactionRepository(self.db)
        for execution in self.executions.list_pending():
            if execution.created_transaction_id is None:
                continue
            tx = tx_repo.get_transaction(execution.created_transaction_id)
            if tx is not None and tx.is_confirmed:
                self.executions.mark_reconciled(execution.manual_execution_id, reconciliation_id)
                if execution.order_ticket_id is not None:
                    OrderTicketRepository(self.db).update_status(execution.order_ticket_id, "reconciled", "approved", "linked transaction confirmed by reconciliation")
                if execution.override_ticket_id is not None:
                    OverrideTicketRepository(self.db).update_status(execution.override_ticket_id, "reconciled")
                count += 1
        return count
