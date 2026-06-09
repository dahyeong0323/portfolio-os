from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from portfolio_os.db import Database, initialize_database
from portfolio_os.importers import AccountSnapshotCSVImporter, load_external_snapshot, write_external_snapshot
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.models import CashBalance, Liability, TaxReserve, Transaction
from portfolio_os.reconciliation import DEFAULT_TOLERANCE, ReconciliationService
from portfolio_os.reconciliation.report_writer import ReconciliationReportWriter
from portfolio_os.repositories import (
    AccountRepository,
    CashBalanceRepository,
    InstrumentRepository,
    LiabilityRepository,
    ReconciliationRepository,
    TaxReserveRepository,
    TransactionRepository,
)
from portfolio_os.serialization import dumps_json
from portfolio_os.state import LedgerStateMachine
from portfolio_os.validators import date_from_text
from portfolio_os.cli.stage2_commands import register_stage2_commands
from portfolio_os.cli.stage3_commands import register_stage3_commands
from portfolio_os.cli.stage4_commands import register_stage4_commands
from portfolio_os.cli.stage5_commands import register_stage5_commands

DEFAULT_DB_PATH = Path("data/portfolio_os.sqlite3")
DEFAULT_SNAPSHOT_DIR = Path("data/imports/account_snapshots")
DEFAULT_REPORT_DIR = Path("data/exports/reconciliation_reports")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio-os")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    subparsers = parser.add_subparsers(required=True)

    init_db = subparsers.add_parser("init-db")
    init_db.set_defaults(func=cmd_init_db)

    status = subparsers.add_parser("ledger-status")
    status.add_argument("--account-id", type=int)
    status.add_argument("--as-of-date")
    status.set_defaults(func=cmd_ledger_status)

    add_account = subparsers.add_parser("add-account")
    add_account.add_argument("--name", required=True)
    add_account.add_argument("--institution", required=True)
    add_account.add_argument("--type", required=True)
    add_account.add_argument("--currency", required=True)
    add_account.add_argument("--masked-number")
    add_account.add_argument("--opened-date")
    add_account.add_argument("--notes")
    add_account.set_defaults(func=cmd_add_account)

    add_instrument = subparsers.add_parser("add-instrument")
    add_instrument.add_argument("--symbol", required=True)
    add_instrument.add_argument("--name", required=True)
    add_instrument.add_argument("--type", required=True)
    add_instrument.add_argument("--currency", required=True)
    add_instrument.add_argument("--exchange")
    add_instrument.add_argument("--isin")
    add_instrument.add_argument("--country")
    add_instrument.add_argument("--fractional", action="store_true")
    add_instrument.set_defaults(func=cmd_add_instrument)

    tx = subparsers.add_parser("record-transaction")
    tx.add_argument("--account-id", type=int, required=True)
    tx.add_argument("--instrument-id", type=int)
    tx.add_argument("--type", required=True)
    tx.add_argument("--trade-date", required=True)
    tx.add_argument("--settlement-date")
    tx.add_argument("--currency", required=True)
    tx.add_argument("--quantity")
    tx.add_argument("--price")
    tx.add_argument("--gross-amount", required=True)
    tx.add_argument("--fee-amount", default="0")
    tx.add_argument("--tax-amount", default="0")
    tx.add_argument("--net-cash-amount", required=True)
    tx.add_argument("--fx-rate-to-base")
    tx.add_argument("--source", default="manual")
    tx.add_argument("--external-ref")
    tx.add_argument("--description")
    tx.set_defaults(func=cmd_record_transaction)

    cash = subparsers.add_parser("record-cash-balance")
    cash.add_argument("--account-id", type=int, required=True)
    cash.add_argument("--as-of-date", required=True)
    cash.add_argument("--currency", required=True)
    cash.add_argument("--amount", required=True)
    cash.add_argument("--source", default="manual")
    cash.add_argument("--external-ref")
    cash.add_argument("--notes")
    cash.set_defaults(func=cmd_record_cash_balance)

    liability = subparsers.add_parser("record-liability")
    liability.add_argument("--account-id", type=int)
    liability.add_argument("--name", required=True)
    liability.add_argument("--type", required=True)
    liability.add_argument("--currency", required=True)
    liability.add_argument("--current-amount", required=True)
    liability.add_argument("--principal-amount")
    liability.add_argument("--interest-rate-annual")
    liability.add_argument("--as-of-date", required=True)
    liability.add_argument("--due-date")
    liability.add_argument("--source", default="manual")
    liability.add_argument("--inactive", action="store_true")
    liability.add_argument("--notes")
    liability.set_defaults(func=cmd_record_liability)

    tax = subparsers.add_parser("record-tax-reserve")
    tax.add_argument("--account-id", type=int)
    tax.add_argument("--tax-year", type=int, required=True)
    tax.add_argument("--type", required=True)
    tax.add_argument("--currency", required=True)
    tax.add_argument("--amount", required=True)
    tax.add_argument("--as-of-date", required=True)
    tax.add_argument("--source", default="manual")
    tax.add_argument("--calculation-basis")
    tax.add_argument("--inactive", action="store_true")
    tax.add_argument("--notes")
    tax.set_defaults(func=cmd_record_tax_reserve)

    import_snapshot = subparsers.add_parser("import-external-snapshot")
    import_snapshot.add_argument("--as-of-date", required=True)
    import_snapshot.add_argument("--account-id", type=int, required=True)
    import_snapshot.add_argument("--positions-csv", type=Path)
    import_snapshot.add_argument("--cash-csv", type=Path)
    import_snapshot.add_argument("--liabilities-csv", type=Path)
    import_snapshot.add_argument("--tax-reserves-csv", type=Path)
    import_snapshot.add_argument("--source", default="csv_import")
    import_snapshot.add_argument("--output-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    import_snapshot.set_defaults(func=cmd_import_external_snapshot)

    run = subparsers.add_parser("run-reconciliation")
    run.add_argument("--snapshot-json", type=Path, required=True)
    run.add_argument("--account-id", type=int)
    run.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    run.set_defaults(func=cmd_run_reconciliation)

    export = subparsers.add_parser("export-reconciliation-report")
    export.add_argument("--output", type=Path)
    export.set_defaults(func=cmd_export_reconciliation_report)
    register_stage2_commands(subparsers)
    register_stage3_commands(subparsers)
    register_stage4_commands(subparsers)
    register_stage5_commands(subparsers)
    return parser


def cmd_init_db(args: argparse.Namespace) -> int:
    initialize_database(args.db)
    print(f"initialized {args.db}")
    return 0


def cmd_ledger_status(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        status = LedgerStateMachine(db).get_current_status(args.account_id, date_from_text(args.as_of_date) if args.as_of_date else None)
        print(status)
    return 0


def cmd_add_account(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        account = AccountRepository(db).create_account(
            account_name=args.name,
            institution_name=args.institution,
            account_type=args.type,
            base_currency=args.currency,
            account_number_masked=args.masked_number,
            opened_date=date_from_text(args.opened_date) if args.opened_date else None,
            notes=args.notes,
        )
        print(dumps_json(account))
    return 0


def cmd_add_instrument(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        instrument = InstrumentRepository(db).create_instrument(
            symbol=args.symbol,
            instrument_name=args.name,
            instrument_type=args.type,
            currency=args.currency,
            exchange=args.exchange,
            isin=args.isin,
            country=args.country,
            is_fractional_allowed=args.fractional,
        )
        print(dumps_json(instrument))
    return 0


def cmd_record_transaction(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        tx = Transaction(
            transaction_id=0,
            account_id=args.account_id,
            instrument_id=args.instrument_id,
            transaction_type=args.type,
            trade_date=date.fromisoformat(args.trade_date),
            settlement_date=date.fromisoformat(args.settlement_date) if args.settlement_date else None,
            currency=args.currency,
            quantity=Decimal(args.quantity) if args.quantity is not None else None,
            price=Decimal(args.price) if args.price is not None else None,
            gross_amount=Decimal(args.gross_amount),
            fee_amount=Decimal(args.fee_amount),
            tax_amount=Decimal(args.tax_amount),
            net_cash_amount=Decimal(args.net_cash_amount),
            fx_rate_to_base=Decimal(args.fx_rate_to_base) if args.fx_rate_to_base else None,
            source=args.source,
            external_ref=args.external_ref,
            description=args.description,
            is_confirmed=False,
            is_voided=False,
            void_reason=None,
        )
        print(dumps_json(TransactionRepository(db).record_transaction(tx)))
    return 0


def cmd_record_cash_balance(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        balance = CashBalance(0, args.account_id, date.fromisoformat(args.as_of_date), args.currency, Decimal(args.amount), args.source, args.external_ref, False, args.notes)
        print(dumps_json(CashBalanceRepository(db).record_cash_balance(balance)))
    return 0


def cmd_record_liability(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        liability = Liability(
            0,
            args.account_id,
            args.name,
            args.type,
            args.currency,
            Decimal(args.principal_amount) if args.principal_amount else None,
            Decimal(args.current_amount),
            Decimal(args.interest_rate_annual) if args.interest_rate_annual else None,
            date.fromisoformat(args.as_of_date),
            date.fromisoformat(args.due_date) if args.due_date else None,
            args.source,
            not args.inactive,
            args.notes,
        )
        print(dumps_json(LiabilityRepository(db).record_liability(liability)))
    return 0


def cmd_record_tax_reserve(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        reserve = TaxReserve(
            0,
            args.account_id,
            args.tax_year,
            args.type,
            args.currency,
            Decimal(args.amount),
            date.fromisoformat(args.as_of_date),
            args.source,
            args.calculation_basis,
            not args.inactive,
            args.notes,
        )
        print(dumps_json(TaxReserveRepository(db).record_tax_reserve(reserve)))
    return 0


def cmd_import_external_snapshot(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        importer = AccountSnapshotCSVImporter(InstrumentRepository(db))
        as_of = date.fromisoformat(args.as_of_date)
        positions = importer.parse_positions_csv(args.positions_csv, args.account_id, as_of) if args.positions_csv else ()
        cash = importer.parse_cash_csv(args.cash_csv, args.account_id, as_of) if args.cash_csv else ()
        liabilities = importer.parse_liabilities_csv(args.liabilities_csv, as_of) if args.liabilities_csv else ()
        tax_reserves = importer.parse_tax_reserves_csv(args.tax_reserves_csv, as_of) if args.tax_reserves_csv else ()
        snapshot = importer.build_external_snapshot(as_of, args.source, positions, cash, liabilities, tax_reserves)
        output_path = write_external_snapshot(snapshot, args.output_dir)
        print(output_path)
    return 0


def cmd_run_reconciliation(args: argparse.Namespace) -> int:
    snapshot = load_external_snapshot(args.snapshot_json)
    with Database(args.db) as db:
        ledger = LedgerSnapshotBuilder(db).build_snapshot(snapshot.as_of_date, args.account_id)
        result = ReconciliationService().run_reconciliation(ledger, snapshot, DEFAULT_TOLERANCE, account_id=args.account_id)
        saved = ReconciliationRepository(db).save_reconciliation_result(result)
        if saved.reconciliation_status == "passed":
            tx_ids = [tx.transaction_id for tx in TransactionRepository(db).list_unconfirmed_transactions(args.account_id)]
            TransactionRepository(db).mark_transactions_confirmed(tx_ids)
            cash_ids = [
                balance.cash_balance_id
                for balance in CashBalanceRepository(db).list_cash_balances(args.account_id, snapshot.as_of_date)
                if not balance.is_reconciled
            ]
            CashBalanceRepository(db).mark_cash_balances_reconciled(cash_ids)
        writer = ReconciliationReportWriter()
        md_path = args.report_dir / f"reconciliation_{saved.reconciliation_id}.md"
        json_path = args.report_dir / f"reconciliation_{saved.reconciliation_id}.json"
        writer.write_markdown_report(saved, md_path)
        writer.write_json_report(saved, json_path)
        print(dumps_json({"reconciliation_id": saved.reconciliation_id, "status": saved.reconciliation_status, "ledger_status": saved.ledger_status_after, "markdown": md_path, "json": json_path}))
    return 0


def cmd_export_reconciliation_report(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        latest = ReconciliationRepository(db).get_latest_reconciliation()
        if latest is None:
            raise SystemExit("no reconciliation snapshots found")
        output = args.output or DEFAULT_REPORT_DIR / f"reconciliation_{latest['reconciliation_id']}_raw.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
