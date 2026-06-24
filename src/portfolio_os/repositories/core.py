from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any, Sequence

from portfolio_os.db.connection import Database
from portfolio_os.models import (
    Account,
    CashBalance,
    Instrument,
    Liability,
    ReconciliationResult,
    TaxReserve,
    Transaction,
)
from portfolio_os.serialization import dumps_json
from portfolio_os.validators import (
    date_from_text,
    date_to_text,
    decimal_from_text,
    decimal_to_text,
    validate_account,
    validate_cash_balance,
    validate_instrument,
    validate_liability,
    validate_tax_reserve,
    validate_transaction,
)


def _bool(value: Any) -> bool:
    return bool(int(value))


def _account_from_row(row: dict[str, Any]) -> Account:
    return Account(
        account_id=row["account_id"],
        account_name=row["account_name"],
        institution_name=row["institution_name"],
        account_type=row["account_type"],
        base_currency=row["base_currency"],
        account_number_masked=row["account_number_masked"],
        is_active=_bool(row["is_active"]),
        opened_date=date_from_text(row["opened_date"]),
        closed_date=date_from_text(row["closed_date"]),
        notes=row["notes"],
    )


def _instrument_from_row(row: dict[str, Any]) -> Instrument:
    return Instrument(
        instrument_id=row["instrument_id"],
        symbol=row["symbol"],
        instrument_name=row["instrument_name"],
        instrument_type=row["instrument_type"],
        exchange=row["exchange"],
        isin=row["isin"],
        currency=row["currency"],
        country=row["country"],
        is_fractional_allowed=_bool(row["is_fractional_allowed"]),
        quantity_precision=row["quantity_precision"],
        price_precision=row["price_precision"],
        is_active=_bool(row["is_active"]),
        notes=row["notes"],
    )


def _transaction_from_row(row: dict[str, Any]) -> Transaction:
    return Transaction(
        transaction_id=row["transaction_id"],
        account_id=row["account_id"],
        instrument_id=row["instrument_id"],
        transaction_type=row["transaction_type"],
        trade_date=date_from_text(row["trade_date"]),
        settlement_date=date_from_text(row["settlement_date"]),
        currency=row["currency"],
        quantity=decimal_from_text(row["quantity"], "quantity", allow_none=True),
        price=decimal_from_text(row["price"], "price", allow_none=True),
        gross_amount=decimal_from_text(row["gross_amount"], "gross_amount"),
        fee_amount=decimal_from_text(row["fee_amount"], "fee_amount"),
        tax_amount=decimal_from_text(row["tax_amount"], "tax_amount"),
        net_cash_amount=decimal_from_text(row["net_cash_amount"], "net_cash_amount"),
        fx_rate_to_base=decimal_from_text(row["fx_rate_to_base"], "fx_rate_to_base", allow_none=True),
        source=row["source"],
        external_ref=row["external_ref"],
        description=row["description"],
        is_confirmed=_bool(row["is_confirmed"]),
        is_voided=_bool(row["is_voided"]),
        void_reason=row["void_reason"],
    )


def _cash_balance_from_row(row: dict[str, Any]) -> CashBalance:
    return CashBalance(
        cash_balance_id=row["cash_balance_id"],
        account_id=row["account_id"],
        as_of_date=date_from_text(row["as_of_date"]),
        currency=row["currency"],
        amount=decimal_from_text(row["amount"], "amount"),
        source=row["source"],
        external_ref=row["external_ref"],
        is_reconciled=_bool(row["is_reconciled"]),
        notes=row["notes"],
    )


def _liability_from_row(row: dict[str, Any]) -> Liability:
    return Liability(
        liability_id=row["liability_id"],
        account_id=row["account_id"],
        liability_name=row["liability_name"],
        liability_type=row["liability_type"],
        currency=row["currency"],
        principal_amount=decimal_from_text(row["principal_amount"], "principal_amount", allow_none=True),
        current_amount=decimal_from_text(row["current_amount"], "current_amount"),
        interest_rate_annual=decimal_from_text(row["interest_rate_annual"], "interest_rate_annual", allow_none=True),
        as_of_date=date_from_text(row["as_of_date"]),
        due_date=date_from_text(row["due_date"]),
        source=row["source"],
        is_active=_bool(row["is_active"]),
        notes=row["notes"],
    )


def _tax_reserve_from_row(row: dict[str, Any]) -> TaxReserve:
    return TaxReserve(
        tax_reserve_id=row["tax_reserve_id"],
        account_id=row["account_id"],
        tax_year=row["tax_year"],
        tax_type=row["tax_type"],
        currency=row["currency"],
        reserved_amount=decimal_from_text(row["reserved_amount"], "reserved_amount"),
        as_of_date=date_from_text(row["as_of_date"]),
        source=row["source"],
        calculation_basis=row["calculation_basis"],
        is_active=_bool(row["is_active"]),
        notes=row["notes"],
    )


class AccountRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_account(
        self,
        account_name: str,
        institution_name: str,
        account_type: str,
        base_currency: str,
        account_number_masked: str | None = None,
        opened_date: date | None = None,
        notes: str | None = None,
    ) -> Account:
        account = Account(0, account_name, institution_name, account_type, base_currency, account_number_masked, True, opened_date, None, notes)
        validate_account(account)
        cursor = self.db.execute(
            """
            INSERT INTO accounts(account_name, institution_name, account_type, base_currency, account_number_masked, opened_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (account_name, institution_name, account_type, base_currency, account_number_masked, date_to_text(opened_date) if opened_date else None, notes),
        )
        self.db.commit()
        return self.get_account(cursor.lastrowid)  # type: ignore[arg-type]

    def get_account(self, account_id: int) -> Account | None:
        row = self.db.fetch_one("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
        return _account_from_row(row) if row else None

    def list_active_accounts(self) -> list[Account]:
        return [_account_from_row(row) for row in self.db.fetch_all("SELECT * FROM accounts WHERE is_active = 1 ORDER BY account_id")]

    def list_all_accounts(self) -> list[Account]:
        return [_account_from_row(row) for row in self.db.fetch_all("SELECT * FROM accounts ORDER BY account_id")]

    def deactivate_account(self, account_id: int, closed_date: date, notes: str | None = None) -> Account:
        self.db.execute(
            "UPDATE accounts SET is_active = 0, closed_date = ?, notes = COALESCE(?, notes), updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE account_id = ?",
            (date_to_text(closed_date), notes, account_id),
        )
        self.db.commit()
        account = self.get_account(account_id)
        if account is None:
            raise ValueError(f"account not found: {account_id}")
        return account


class InstrumentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_instrument(
        self,
        symbol: str,
        instrument_name: str,
        instrument_type: str,
        currency: str,
        exchange: str | None = None,
        isin: str | None = None,
        country: str | None = None,
        is_fractional_allowed: bool = False,
        quantity_precision: int = 6,
        price_precision: int = 6,
        notes: str | None = None,
    ) -> Instrument:
        instrument = Instrument(0, symbol, instrument_name, instrument_type, exchange, isin, currency, country, is_fractional_allowed, quantity_precision, price_precision, True, notes)
        validate_instrument(instrument)
        cursor = self.db.execute(
            """
            INSERT INTO instruments(symbol, instrument_name, instrument_type, exchange, isin, currency, country, is_fractional_allowed, quantity_precision, price_precision, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol, instrument_name, instrument_type, exchange, isin, currency, country, int(is_fractional_allowed), quantity_precision, price_precision, notes),
        )
        self.db.commit()
        return self.get_instrument(cursor.lastrowid)  # type: ignore[arg-type]

    def get_instrument(self, instrument_id: int) -> Instrument | None:
        row = self.db.fetch_one("SELECT * FROM instruments WHERE instrument_id = ?", (instrument_id,))
        return _instrument_from_row(row) if row else None

    def find_by_symbol(self, symbol: str, currency: str | None = None, exchange: str | None = None) -> list[Instrument]:
        sql = "SELECT * FROM instruments WHERE symbol = ? AND is_active = 1"
        params: list[Any] = [symbol]
        if currency is not None:
            sql += " AND currency = ?"
            params.append(currency)
        if exchange is not None:
            sql += " AND exchange = ?"
            params.append(exchange)
        sql += " ORDER BY instrument_id"
        return [_instrument_from_row(row) for row in self.db.fetch_all(sql, params)]

    def list_active_instruments(self) -> list[Instrument]:
        return [_instrument_from_row(row) for row in self.db.fetch_all("SELECT * FROM instruments WHERE is_active = 1 ORDER BY symbol")]

    def list_all_instruments(self) -> list[Instrument]:
        return [_instrument_from_row(row) for row in self.db.fetch_all("SELECT * FROM instruments ORDER BY symbol, instrument_id")]


class TransactionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_transaction(self, transaction: Transaction) -> Transaction:
        validate_transaction(transaction)
        cursor = self.db.execute(
            """
            INSERT INTO transactions(
                account_id, instrument_id, transaction_type, trade_date, settlement_date, currency,
                quantity, price, gross_amount, fee_amount, tax_amount, net_cash_amount, fx_rate_to_base,
                source, external_ref, description, is_confirmed, is_voided, void_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.account_id,
                transaction.instrument_id,
                transaction.transaction_type,
                date_to_text(transaction.trade_date),
                date_to_text(transaction.settlement_date) if transaction.settlement_date else None,
                transaction.currency,
                decimal_to_text(transaction.quantity, "quantity", allow_none=True),
                decimal_to_text(transaction.price, "price", allow_none=True),
                decimal_to_text(transaction.gross_amount, "gross_amount"),
                decimal_to_text(transaction.fee_amount, "fee_amount"),
                decimal_to_text(transaction.tax_amount, "tax_amount"),
                decimal_to_text(transaction.net_cash_amount, "net_cash_amount"),
                decimal_to_text(transaction.fx_rate_to_base, "fx_rate_to_base", allow_none=True),
                transaction.source,
                transaction.external_ref,
                transaction.description,
                int(transaction.is_confirmed),
                int(transaction.is_voided),
                transaction.void_reason,
            ),
        )
        self.db.commit()
        return self.get_transaction(cursor.lastrowid)  # type: ignore[arg-type]

    def get_transaction(self, transaction_id: int) -> Transaction | None:
        row = self.db.fetch_one("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
        return _transaction_from_row(row) if row else None

    def list_transactions(
        self,
        account_id: int | None = None,
        through_date: date | None = None,
        include_voided: bool = False,
    ) -> list[Transaction]:
        sql = "SELECT * FROM transactions WHERE 1 = 1"
        params: list[Any] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if through_date is not None:
            sql += " AND trade_date <= ?"
            params.append(date_to_text(through_date))
        if not include_voided:
            sql += " AND is_voided = 0"
        sql += " ORDER BY trade_date, transaction_id"
        return [_transaction_from_row(row) for row in self.db.fetch_all(sql, params)]

    def list_unconfirmed_transactions(
        self,
        account_id: int | None = None,
        through_date: date | None = None,
    ) -> list[Transaction]:
        sql = "SELECT * FROM transactions WHERE is_confirmed = 0 AND is_voided = 0"
        params: list[Any] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if through_date is not None:
            sql += " AND trade_date <= ?"
            params.append(date_to_text(through_date))
        return [_transaction_from_row(row) for row in self.db.fetch_all(sql, params)]

    def void_transaction(self, transaction_id: int, void_reason: str) -> Transaction:
        if not void_reason:
            raise ValueError("void_reason is required")
        self.db.execute(
            "UPDATE transactions SET is_voided = 1, void_reason = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE transaction_id = ?",
            (void_reason, transaction_id),
        )
        self.db.commit()
        tx = self.get_transaction(transaction_id)
        if tx is None:
            raise ValueError(f"transaction not found: {transaction_id}")
        return tx

    def mark_transactions_confirmed(self, transaction_ids: Sequence[int]) -> int:
        if not transaction_ids:
            return 0
        placeholders = ",".join("?" for _ in transaction_ids)
        cursor = self.db.execute(f"UPDATE transactions SET is_confirmed = 1 WHERE transaction_id IN ({placeholders})", tuple(transaction_ids))
        self.db.commit()
        return cursor.rowcount


class CashBalanceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_cash_balance(self, cash_balance: CashBalance) -> CashBalance:
        validate_cash_balance(cash_balance)
        cursor = self.db.execute(
            """
            INSERT INTO cash_balances(account_id, as_of_date, currency, amount, source, external_ref, is_reconciled, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cash_balance.account_id,
                date_to_text(cash_balance.as_of_date),
                cash_balance.currency,
                decimal_to_text(cash_balance.amount, "amount"),
                cash_balance.source,
                cash_balance.external_ref,
                int(cash_balance.is_reconciled),
                cash_balance.notes,
            ),
        )
        self.db.commit()
        return self.get_cash_balance(cursor.lastrowid)  # type: ignore[arg-type]

    def get_cash_balance(self, cash_balance_id: int) -> CashBalance | None:
        row = self.db.fetch_one("SELECT * FROM cash_balances WHERE cash_balance_id = ?", (cash_balance_id,))
        return _cash_balance_from_row(row) if row else None

    def list_cash_balances(self, account_id: int | None = None, through_date: date | None = None) -> list[CashBalance]:
        sql = "SELECT * FROM cash_balances WHERE 1 = 1"
        params: list[Any] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if through_date is not None:
            sql += " AND as_of_date <= ?"
            params.append(date_to_text(through_date))
        sql += " ORDER BY as_of_date, cash_balance_id"
        return [_cash_balance_from_row(row) for row in self.db.fetch_all(sql, params)]

    def mark_cash_balances_reconciled(self, cash_balance_ids: Sequence[int]) -> int:
        if not cash_balance_ids:
            return 0
        placeholders = ",".join("?" for _ in cash_balance_ids)
        cursor = self.db.execute(f"UPDATE cash_balances SET is_reconciled = 1 WHERE cash_balance_id IN ({placeholders})", tuple(cash_balance_ids))
        self.db.commit()
        return cursor.rowcount


class LiabilityRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_liability(self, liability: Liability) -> Liability:
        validate_liability(liability)
        cursor = self.db.execute(
            """
            INSERT INTO liabilities(account_id, liability_name, liability_type, currency, principal_amount, current_amount, interest_rate_annual, as_of_date, due_date, source, is_active, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                liability.account_id,
                liability.liability_name,
                liability.liability_type,
                liability.currency,
                decimal_to_text(liability.principal_amount, "principal_amount", allow_none=True),
                decimal_to_text(liability.current_amount, "current_amount"),
                decimal_to_text(liability.interest_rate_annual, "interest_rate_annual", allow_none=True),
                date_to_text(liability.as_of_date),
                date_to_text(liability.due_date) if liability.due_date else None,
                liability.source,
                int(liability.is_active),
                liability.notes,
            ),
        )
        self.db.commit()
        return self.get_liability(cursor.lastrowid)  # type: ignore[arg-type]

    def get_liability(self, liability_id: int) -> Liability | None:
        row = self.db.fetch_one("SELECT * FROM liabilities WHERE liability_id = ?", (liability_id,))
        return _liability_from_row(row) if row else None

    def list_liabilities(self, account_id: int | None = None, through_date: date | None = None) -> list[Liability]:
        sql = "SELECT * FROM liabilities WHERE 1 = 1"
        params: list[Any] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if through_date is not None:
            sql += " AND as_of_date <= ?"
            params.append(date_to_text(through_date))
        sql += " ORDER BY as_of_date, liability_id"
        return [_liability_from_row(row) for row in self.db.fetch_all(sql, params)]


class TaxReserveRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_tax_reserve(self, tax_reserve: TaxReserve) -> TaxReserve:
        validate_tax_reserve(tax_reserve)
        cursor = self.db.execute(
            """
            INSERT INTO tax_reserves(account_id, tax_year, tax_type, currency, reserved_amount, as_of_date, source, calculation_basis, is_active, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tax_reserve.account_id,
                tax_reserve.tax_year,
                tax_reserve.tax_type,
                tax_reserve.currency,
                decimal_to_text(tax_reserve.reserved_amount, "reserved_amount"),
                date_to_text(tax_reserve.as_of_date),
                tax_reserve.source,
                tax_reserve.calculation_basis,
                int(tax_reserve.is_active),
                tax_reserve.notes,
            ),
        )
        self.db.commit()
        return self.get_tax_reserve(cursor.lastrowid)  # type: ignore[arg-type]

    def get_tax_reserve(self, tax_reserve_id: int) -> TaxReserve | None:
        row = self.db.fetch_one("SELECT * FROM tax_reserves WHERE tax_reserve_id = ?", (tax_reserve_id,))
        return _tax_reserve_from_row(row) if row else None

    def list_tax_reserves(self, account_id: int | None = None, through_date: date | None = None) -> list[TaxReserve]:
        sql = "SELECT * FROM tax_reserves WHERE 1 = 1"
        params: list[Any] = []
        if account_id is not None:
            sql += " AND account_id = ?"
            params.append(account_id)
        if through_date is not None:
            sql += " AND as_of_date <= ?"
            params.append(date_to_text(through_date))
        sql += " ORDER BY as_of_date, tax_reserve_id"
        return [_tax_reserve_from_row(row) for row in self.db.fetch_all(sql, params)]


class ReconciliationRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_reconciliation_result(self, result: ReconciliationResult) -> ReconciliationResult:
        position_over = [d for d in result.position_differences if not d.within_tolerance]
        cash_over = [d for d in result.cash_differences if not d.within_tolerance]
        liability_over = [d for d in result.liability_differences if not d.within_tolerance]
        tax_over = [d for d in result.tax_reserve_differences if not d.within_tolerance]
        total_abs_cash = sum((abs(d.difference) for d in cash_over), Decimal("0"))
        cursor = self.db.execute(
            """
            INSERT INTO reconciliation_snapshots(
                account_id, as_of_date, started_at, completed_at, ledger_status_before, ledger_status_after,
                reconciliation_status, snapshot_source, position_diff_count, cash_diff_count,
                liability_diff_count, tax_reserve_diff_count, total_abs_cash_diff_base,
                tolerance_cash_abs, tolerance_quantity_abs, expected_positions_json, actual_positions_json,
                position_diffs_json, expected_cash_json, actual_cash_json, cash_diffs_json,
                expected_liabilities_json, actual_liabilities_json, liability_diffs_json,
                expected_tax_reserves_json, actual_tax_reserves_json, tax_reserve_diffs_json, failure_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.account_id,
                date_to_text(result.as_of_date),
                result.started_at.isoformat().replace("+00:00", "Z"),
                result.completed_at.isoformat().replace("+00:00", "Z"),
                result.ledger_status_before,
                result.ledger_status_after,
                result.reconciliation_status,
                result.snapshot_source,
                len(position_over),
                len(cash_over),
                len(liability_over),
                len(tax_over),
                decimal_to_text(total_abs_cash, "total_abs_cash_diff_base"),
                decimal_to_text(result.tolerance.cash_abs, "tolerance_cash_abs"),
                decimal_to_text(result.tolerance.quantity_abs, "tolerance_quantity_abs"),
                dumps_json(result.expected_positions),
                dumps_json(result.actual_positions),
                dumps_json(result.position_differences),
                dumps_json(result.expected_cash),
                dumps_json(result.actual_cash),
                dumps_json(result.cash_differences),
                dumps_json(result.expected_liabilities),
                dumps_json(result.actual_liabilities),
                dumps_json(result.liability_differences),
                dumps_json(result.expected_tax_reserves),
                dumps_json(result.actual_tax_reserves),
                dumps_json(result.tax_reserve_differences),
                result.failure_reason,
            ),
        )
        self.db.commit()
        return replace(result, reconciliation_id=cursor.lastrowid)

    def get_latest_reconciliation(self, account_id: int | None = None) -> dict[str, Any] | None:
        if account_id is None:
            return self.db.fetch_one("SELECT * FROM reconciliation_snapshots ORDER BY completed_at DESC, reconciliation_id DESC LIMIT 1")
        return self.db.fetch_one(
            "SELECT * FROM reconciliation_snapshots WHERE account_id = ? OR account_id IS NULL ORDER BY completed_at DESC, reconciliation_id DESC LIMIT 1",
            (account_id,),
        )

    def get_reconciliation(self, reconciliation_id: int) -> dict[str, Any] | None:
        return self.db.fetch_one(
            "SELECT * FROM reconciliation_snapshots WHERE reconciliation_id = ?",
            (reconciliation_id,),
        )

    def get_latest_reconciled(self, account_id: int | None = None) -> dict[str, Any] | None:
        if account_id is None:
            return self.db.fetch_one(
                "SELECT * FROM reconciliation_snapshots WHERE ledger_status_after = 'reconciled' "
                "ORDER BY completed_at DESC, reconciliation_id DESC LIMIT 1"
            )
        return self.db.fetch_one(
            "SELECT * FROM reconciliation_snapshots "
            "WHERE ledger_status_after = 'reconciled' AND (account_id = ? OR account_id IS NULL) "
            "ORDER BY completed_at DESC, reconciliation_id DESC LIMIT 1",
            (account_id,),
        )

    def list_reconciliations(self, account_id: int | None = None) -> list[dict[str, Any]]:
        if account_id is None:
            return self.db.fetch_all("SELECT * FROM reconciliation_snapshots ORDER BY completed_at DESC, reconciliation_id DESC")
        return self.db.fetch_all(
            "SELECT * FROM reconciliation_snapshots WHERE account_id = ? OR account_id IS NULL ORDER BY completed_at DESC, reconciliation_id DESC",
            (account_id,),
        )
