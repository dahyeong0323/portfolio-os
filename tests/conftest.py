from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from portfolio_os.db import Database, initialize_database
from portfolio_os.models import CashBalance, Transaction
from portfolio_os.repositories import AccountRepository, CashBalanceRepository, InstrumentRepository, TransactionRepository


@pytest.fixture
def db(tmp_path: Path) -> Database:
    db_path = tmp_path / "portfolio_os.sqlite3"
    initialize_database(db_path)
    database = Database(db_path)
    database.connect()
    try:
        yield database
    finally:
        database.close()


def seed_account(db: Database) -> int:
    return AccountRepository(db).create_account("Brokerage", "Test Bank", "securities", "USD").account_id


def seed_instrument(db: Database, symbol: str = "AAPL", exchange: str | None = "NASDAQ") -> int:
    return InstrumentRepository(db).create_instrument(symbol, f"{symbol} Inc.", "stock", "USD", exchange=exchange).instrument_id


def seed_cash_anchor(db: Database, account_id: int, amount: str = "10000", as_of: date = date(2026, 1, 1)) -> int:
    return CashBalanceRepository(db).record_cash_balance(
        CashBalance(0, account_id, as_of, "USD", Decimal(amount), "manual", None, False, None)
    ).cash_balance_id


def seed_buy(db: Database, account_id: int, instrument_id: int) -> int:
    return TransactionRepository(db).record_transaction(
        Transaction(
            transaction_id=0,
            account_id=account_id,
            instrument_id=instrument_id,
            transaction_type="buy",
            trade_date=date(2026, 1, 2),
            settlement_date=None,
            currency="USD",
            quantity=Decimal("1"),
            price=Decimal("100"),
            gross_amount=Decimal("100"),
            fee_amount=Decimal("0"),
            tax_amount=Decimal("0"),
            net_cash_amount=Decimal("-100"),
            fx_rate_to_base=None,
            source="manual",
            external_ref=None,
            description=None,
            is_confirmed=False,
            is_voided=False,
            void_reason=None,
        )
    ).transaction_id
