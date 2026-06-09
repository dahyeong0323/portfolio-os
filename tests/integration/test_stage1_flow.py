from __future__ import annotations

from datetime import date
from decimal import Decimal

from portfolio_os.importers import AccountSnapshotCSVImporter, write_external_snapshot
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import ExternalAccountSnapshot, ExternalCash, ExternalPosition, Transaction
from portfolio_os.reconciliation import ReconciliationService
from portfolio_os.repositories import CashBalanceRepository, ReconciliationRepository, TransactionRepository
from portfolio_os.state import LedgerStateMachine
from portfolio_os.validators import utc_now
from tests.conftest import seed_account, seed_buy, seed_cash_anchor, seed_instrument


def build_external(account_id: int, instrument_id: int, cash_amount: str = "9900", quantity: str = "1") -> ExternalAccountSnapshot:
    return ExternalAccountSnapshot(
        as_of_date=date(2026, 1, 3),
        source="manual",
        positions=(ExternalPosition(account_id, "AAPL", "USD", Decimal(quantity), "NASDAQ", instrument_id),),
        cash=(ExternalCash(account_id, "USD", Decimal(cash_amount)),),
        liabilities=(),
        tax_reserves=(),
        received_at=utc_now(),
    )


def mark_reconciled_after_pass(db, account_id: int, as_of: date) -> None:
    tx_ids = [tx.transaction_id for tx in TransactionRepository(db).list_unconfirmed_transactions(account_id)]
    TransactionRepository(db).mark_transactions_confirmed(tx_ids)
    cash_ids = [cash.cash_balance_id for cash in CashBalanceRepository(db).list_cash_balances(account_id, as_of) if not cash.is_reconciled]
    CashBalanceRepository(db).mark_cash_balances_reconciled(cash_ids)


def test_reconciliation_pass_and_status_reconciled(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)

    ledger = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id)
    assert ledger.cash[0].amount == Decimal("9900")
    result = ReconciliationService().run_reconciliation(ledger, build_external(account_id, instrument_id), account_id=account_id)
    saved = ReconciliationRepository(db).save_reconciliation_result(result)
    assert saved.reconciliation_status == "passed"
    mark_reconciled_after_pass(db, account_id, date(2026, 1, 3))
    assert LedgerStateMachine(db).get_current_status(account_id, date(2026, 1, 3)) == "reconciled"


def test_reconciliation_cash_diff_fails_broken(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)

    ledger = LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id)
    result = ReconciliationService().run_reconciliation(ledger, build_external(account_id, instrument_id, cash_amount="9800"), account_id=account_id)
    saved = ReconciliationRepository(db).save_reconciliation_result(result)
    assert saved.reconciliation_status == "failed"
    assert LedgerStateMachine(db).get_current_status(account_id, date(2026, 1, 3)) == "broken"


def test_broken_to_correction_to_reconciled_recovery(db) -> None:
    account_id = seed_account(db)
    instrument_id = seed_instrument(db)
    seed_cash_anchor(db, account_id)
    seed_buy(db, account_id, instrument_id)
    failed = ReconciliationService().run_reconciliation(
        LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id),
        build_external(account_id, instrument_id, cash_amount="9800"),
        account_id=account_id,
    )
    ReconciliationRepository(db).save_reconciliation_result(failed)

    correction = Transaction(
        0,
        account_id,
        None,
        "correction",
        date(2026, 1, 3),
        None,
        "USD",
        None,
        None,
        Decimal("-100"),
        Decimal("0"),
        Decimal("0"),
        Decimal("-100"),
        None,
        "system_correction",
        None,
        "correction for transaction 1",
        False,
        False,
        None,
    )
    TransactionRepository(db).record_transaction(correction)
    assert LedgerStateMachine(db).get_current_status(account_id, date(2026, 1, 3)) == "provisional"
    passed = ReconciliationService().run_reconciliation(
        LedgerSnapshotBuilder(db).build_snapshot(date(2026, 1, 3), account_id),
        build_external(account_id, instrument_id, cash_amount="9800"),
        account_id=account_id,
    )
    saved = ReconciliationRepository(db).save_reconciliation_result(passed)
    assert saved.reconciliation_status == "passed"
    mark_reconciled_after_pass(db, account_id, date(2026, 1, 3))
    assert LedgerStateMachine(db).get_current_status(account_id, date(2026, 1, 3)) == "reconciled"


def test_external_snapshot_cash_is_not_inserted_into_cash_balances(db, tmp_path) -> None:
    account_id = seed_account(db)
    cash_csv = tmp_path / "cash.csv"
    cash_csv.write_text("currency,amount\nUSD,12345\n", encoding="utf-8")
    importer = AccountSnapshotCSVImporter()
    snapshot = importer.build_external_snapshot(
        date(2026, 1, 3),
        "csv_import",
        (),
        importer.parse_cash_csv(cash_csv, account_id, date(2026, 1, 3)),
        (),
        (),
    )
    artifact = write_external_snapshot(snapshot, tmp_path)
    assert artifact.exists()
    rows = db.fetch_all("SELECT * FROM cash_balances")
    assert rows == []
