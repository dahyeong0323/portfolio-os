from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from portfolio_os.execution import ManualExecutionRepository, ManualExecutionService
from portfolio_os.importers.csv_snapshot_importer import AccountSnapshotCSVImporter
from portfolio_os.intents import TransactionIntentService
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ExternalCash
from portfolio_os.reconciliation import ReconciliationService
from portfolio_os.repositories import CashBalanceRepository, ReconciliationRepository, TransactionRepository
from portfolio_os.risk import RiskEngine, seed_default_risk_policy
from portfolio_os.risk.repositories import PricingRepository
from portfolio_os.tickets import OrderTicketRepository, OrderTicketService
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_cash_anchor, seed_instrument


def reconcile_empty_account(db, account_id: int, as_of: date) -> None:
    ledger = LedgerSnapshotBuilder(db).build_snapshot(as_of, account_id)
    snapshot = ExternalAccountSnapshot(as_of, "manual", (), (ExternalCash(account_id, "USD", Decimal("10000")),), (), (), utc_now())
    result = ReconciliationService().run_reconciliation(ledger, snapshot, account_id=account_id)
    saved = ReconciliationRepository(db).save_reconciliation_result(result)
    assert saved.reconciliation_status == "passed"
    cash_ids = [cash.cash_balance_id for cash in CashBalanceRepository(db).list_cash_balances(account_id, as_of)]
    CashBalanceRepository(db).mark_cash_balances_reconciled(cash_ids)


def test_buy_ticket_approval_and_manual_execution_creates_provisional_transaction(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    reconcile_empty_account(db, account_id, date(2026, 1, 1))
    policy_id = seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    intent = TransactionIntentService(db).create_intent(account_id, instrument_id, "buy", "USD", Decimal("1"), None, Decimal("100"), "test buy")
    ledger = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id)
    result = RiskEngine(db).validate_and_persist(intent, ledger, policy_id, date(2026, 1, 2))
    assert result.validation_status == "passed"
    ticket = OrderTicketService(db).create_ticket_from_validation(result.risk_validation_id, utc_now() + timedelta(days=1))
    approved = OrderTicketService(db).approve_ticket(ticket.order_ticket_id, "approved for test")
    assert approved.status == "approved"
    execution = ManualExecutionService(db).log_execution_for_ticket(approved.order_ticket_id, Decimal("1"), Decimal("100"), Decimal("0"), Decimal("0"), datetime(2026, 1, 2, tzinfo=timezone.utc))
    assert execution.execution_status == "pending_reconciliation"
    tx = TransactionRepository(db).get_transaction(execution.created_transaction_id)
    assert tx is not None
    assert tx.is_confirmed is False
    assert LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id).ledger_status == "provisional"


def test_reconciliation_confirms_only_linked_confirmed_execution(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    reconcile_empty_account(db, account_id, date(2026, 1, 1))
    policy_id = seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))

    approved_tickets = []
    for _ in range(2):
        intent = TransactionIntentService(db).create_intent(account_id, instrument_id, "buy", "USD", Decimal("1"), None, Decimal("100"), "test buy")
        result = RiskEngine(db).validate_and_persist(intent, LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id), policy_id, date(2026, 1, 2))
        ticket = OrderTicketService(db).create_ticket_from_validation(result.risk_validation_id, utc_now() + timedelta(days=1))
        approved_tickets.append(OrderTicketService(db).approve_ticket(ticket.order_ticket_id, "approved"))

    executions = [
        ManualExecutionService(db).log_execution_for_ticket(ticket.order_ticket_id, Decimal("1"), Decimal("100"), Decimal("0"), Decimal("0"), datetime(2026, 1, 2, tzinfo=timezone.utc))
        for ticket in approved_tickets
    ]

    TransactionRepository(db).mark_transactions_confirmed([executions[0].created_transaction_id])
    from portfolio_os.models import ReconciliationResult
    from portfolio_os.reconciliation import DEFAULT_TOLERANCE

    now = utc_now()
    saved = ReconciliationRepository(db).save_reconciliation_result(
        ReconciliationResult(
            None,
            account_id,
            date(2026, 1, 2),
            now,
            now,
            "provisional",
            "reconciled",
            "passed",
            "manual",
            (),
            (),
            (),
            (),
            (),
            (),
                (),
                (),
                (),
                (),
                (),
                (),
                DEFAULT_TOLERANCE,
                None,
            )
    )
    confirmed = ManualExecutionService(db).mark_reconciled_after_passed_reconciliation(saved.reconciliation_id)
    assert confirmed == 1
    assert ManualExecutionRepository(db).get(executions[0].manual_execution_id).execution_status == "reconciled"
    assert ManualExecutionRepository(db).get(executions[1].manual_execution_id).execution_status == "pending_reconciliation"


def test_broken_ledger_blocks_official_ticket_but_allows_override(db) -> None:
    from portfolio_os.override import OverrideService

    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_default_risk_policy(db, "USD")
    PricingRepository(db).record_price(instrument_id, date(2026, 1, 2), "USD", Decimal("100"))
    broken_snapshot = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 2), account_id)
    object.__setattr__(broken_snapshot, "ledger_status", "broken")
    intent = TransactionIntentService(db).create_intent(account_id, instrument_id, "buy", "USD", Decimal("1"), None, Decimal("100"), "test")
    result = RiskEngine(db).validate_intent(intent, broken_snapshot)
    assert result.validation_status == "rejected"
    override = OverrideService(db).declare_override("no_sync", account_id, instrument_id, "buy", Decimal("1"), None, "USD", "must trade outside official loop")
    assert override.status == "risk_warned"
