from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from portfolio_os.db.connection import Database
from portfolio_os.execution.repository import ManualExecutionRepository
from portfolio_os.journal.service import DecisionJournalService
from portfolio_os.models import Transaction
from portfolio_os.override.repository import OverrideTicketRepository
from portfolio_os.repositories import ReconciliationRepository, TransactionRepository
from portfolio_os.tickets.repository import OrderTicketRepository
from portfolio_os.validators import date_from_text


@dataclass(frozen=True)
class ConfirmationSkippedExecution:
    execution_id: int | None
    reason: str
    detail: str | None = None


@dataclass(frozen=True)
class ConfirmationRunResult:
    confirmation_run_id: str
    reconciliation_id_used: int
    total_pending_checked: int
    confirmed_execution_ids: list[int]
    still_pending_execution_ids: list[int]
    failed_execution_ids: list[int]
    skipped_executions: list[ConfirmationSkippedExecution]
    explanation: str


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
        notes: str | None = None,
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
            notes=notes,
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

    def confirm_after_reconciliation(
        self,
        *,
        confirmation_run_id: str,
        reconciliation_id: int | None = None,
        account_id: int | None = None,
        as_of_date: date | None = None,
        execution_ids: Sequence[int] | None = None,
    ) -> ConfirmationRunResult:
        reconciliation = self._resolve_reconciliation(reconciliation_id, account_id, as_of_date, execution_ids)
        reconciliation_as_of = date_from_text(reconciliation["as_of_date"])
        reconciliation_account_id = reconciliation["account_id"]
        if reconciliation["reconciliation_status"] != "passed":
            raise ValueError(f"reconciliation must be passed, got {reconciliation['reconciliation_status']}")

        executions, skipped = self._candidate_executions(execution_ids)
        if execution_ids is None:
            executions = [
                execution for execution in executions
                if (account_id is None or execution.account_id == account_id)
                and (reconciliation_account_id is None or execution.account_id == reconciliation_account_id)
            ]

        confirmed: list[int] = []
        still_pending: list[int] = []
        failed: list[int] = []
        tx_repo = TransactionRepository(self.db)
        tickets = OrderTicketRepository(self.db)

        for execution in executions:
            if execution.execution_status != "pending_reconciliation":
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "execution_not_pending", execution.execution_status))
                continue
            if execution.override_ticket_id is not None:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "override_execution_deferred"))
                continue
            if account_id is not None and execution.account_id != account_id:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "account_scope_mismatch"))
                continue
            if reconciliation_account_id is not None and execution.account_id != reconciliation_account_id:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "reconciliation_account_mismatch"))
                continue
            if execution.executed_at.date() > reconciliation_as_of:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "execution_after_reconciliation"))
                continue
            if execution.created_transaction_id is None:
                still_pending.append(execution.manual_execution_id)
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "missing_provisional_transaction"))
                continue
            tx = tx_repo.get_transaction(execution.created_transaction_id)
            if tx is None:
                still_pending.append(execution.manual_execution_id)
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "provisional_transaction_not_found"))
                continue
            if tx.account_id != execution.account_id:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "transaction_account_mismatch"))
                continue
            if tx.trade_date > reconciliation_as_of:
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "transaction_after_reconciliation"))
                continue
            if not tx.is_confirmed:
                still_pending.append(execution.manual_execution_id)
                skipped.append(ConfirmationSkippedExecution(execution.manual_execution_id, "transaction_not_confirmed"))
                continue
            try:
                self.executions.mark_reconciled(execution.manual_execution_id, reconciliation["reconciliation_id"])
                if execution.order_ticket_id is not None:
                    tickets.update_status(execution.order_ticket_id, "reconciled", "approved", "linked transaction confirmed by reconciliation")
                confirmed.append(execution.manual_execution_id)
            except ValueError:
                failed.append(execution.manual_execution_id)

        return ConfirmationRunResult(
            confirmation_run_id=confirmation_run_id,
            reconciliation_id_used=reconciliation["reconciliation_id"],
            total_pending_checked=len(executions),
            confirmed_execution_ids=confirmed,
            still_pending_execution_ids=still_pending,
            failed_execution_ids=failed,
            skipped_executions=skipped,
            explanation="Pending manual executions were checked against passed reconciliation evidence. No broker order was placed and no new transaction was created.",
        )

    def _resolve_reconciliation(
        self,
        reconciliation_id: int | None,
        account_id: int | None,
        as_of_date: date | None,
        execution_ids: Sequence[int] | None,
    ) -> dict:
        repo = ReconciliationRepository(self.db)
        if reconciliation_id is not None:
            row = repo.get_reconciliation(reconciliation_id)
            if row is None:
                raise ValueError("reconciliation not found")
            if account_id is not None and row["account_id"] is not None and row["account_id"] != account_id:
                raise ValueError("reconciliation account does not match requested account")
            if as_of_date is not None and date_from_text(row["as_of_date"]) != as_of_date:
                raise ValueError("reconciliation date does not match requested as_of_date")
            return row

        if account_id is None and not execution_ids:
            raise ValueError("confirmation requires reconciliation_id, account_id, or execution_ids")

        candidates = repo.list_reconciliations(account_id)
        if as_of_date is not None:
            candidates = [row for row in candidates if date_from_text(row["as_of_date"]) == as_of_date]
        if not candidates:
            raise ValueError("matching reconciliation not found")
        return candidates[0]

    def _candidate_executions(self, execution_ids: Sequence[int] | None):
        skipped: list[ConfirmationSkippedExecution] = []
        if execution_ids:
            executions = []
            for execution_id in execution_ids:
                try:
                    executions.append(self.executions.get(execution_id))
                except ValueError:
                    skipped.append(ConfirmationSkippedExecution(execution_id, "execution_not_found"))
            return executions, skipped
        return self.executions.list_pending(), skipped
