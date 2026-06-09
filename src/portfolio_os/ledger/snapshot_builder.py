from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from portfolio_os.db.connection import Database
from portfolio_os.models import LedgerCash, LedgerLiability, LedgerPosition, LedgerSnapshot, LedgerTaxReserve
from portfolio_os.repositories import CashBalanceRepository, InstrumentRepository, LiabilityRepository, TaxReserveRepository, TransactionRepository
from portfolio_os.state.state_machine import LedgerStateMachine
from portfolio_os.validators import utc_now


class LedgerSnapshotBuilder:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.transactions = TransactionRepository(db)
        self.cash_balances = CashBalanceRepository(db)
        self.liabilities = LiabilityRepository(db)
        self.tax_reserves = TaxReserveRepository(db)
        self.instruments = InstrumentRepository(db)
        self.state_machine = LedgerStateMachine(db)

    def build_snapshot(self, as_of_date: date, account_id: int | None = None) -> LedgerSnapshot:
        return LedgerSnapshot(
            as_of_date=as_of_date,
            ledger_status=self.state_machine.get_current_status(account_id=account_id, as_of_date=as_of_date),
            positions=self.build_positions(as_of_date, account_id),
            cash=self.build_cash(as_of_date, account_id),
            liabilities=self.build_liabilities(as_of_date, account_id),
            tax_reserves=self.build_tax_reserves(as_of_date, account_id),
            generated_at=utc_now(),
        )

    def build_positions(self, as_of_date: date, account_id: int | None = None) -> tuple[LedgerPosition, ...]:
        quantities: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal("0"))
        buy_qty: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal("0"))
        buy_cost: dict[tuple[int, int], Decimal] = defaultdict(lambda: Decimal("0"))
        for tx in self.transactions.list_transactions(account_id=account_id, through_date=as_of_date):
            if tx.instrument_id is None or tx.quantity is None:
                continue
            key = (tx.account_id, tx.instrument_id)
            quantities[key] += tx.quantity
            if tx.transaction_type == "buy":
                buy_qty[key] += tx.quantity
                buy_cost[key] += abs(tx.net_cash_amount)
        positions: list[LedgerPosition] = []
        for (acct_id, instrument_id), quantity in sorted(quantities.items()):
            if quantity == 0:
                continue
            instrument = self.instruments.get_instrument(instrument_id)
            if instrument is None:
                continue
            average_cost = buy_cost[(acct_id, instrument_id)] / buy_qty[(acct_id, instrument_id)] if buy_qty[(acct_id, instrument_id)] else None
            positions.append(
                LedgerPosition(
                    account_id=acct_id,
                    instrument_id=instrument_id,
                    symbol=instrument.symbol,
                    currency=instrument.currency,
                    quantity=quantity,
                    average_cost=average_cost,
                )
            )
        return tuple(positions)

    def build_cash(self, as_of_date: date, account_id: int | None = None) -> tuple[LedgerCash, ...]:
        anchors: dict[tuple[int, str], tuple[date, Decimal]] = {}
        for balance in self.cash_balances.list_cash_balances(account_id=account_id, through_date=as_of_date):
            key = (balance.account_id, balance.currency)
            current = anchors.get(key)
            if current is None or balance.as_of_date >= current[0]:
                anchors[key] = (balance.as_of_date, balance.amount)

        amounts: dict[tuple[int, str], Decimal] = {}
        for key, (_anchor_date, amount) in anchors.items():
            amounts[key] = amount

        for tx in self.transactions.list_transactions(account_id=account_id, through_date=as_of_date):
            key = (tx.account_id, tx.currency)
            anchor = anchors.get(key)
            if anchor is not None and tx.trade_date <= anchor[0]:
                continue
            amounts[key] = amounts.get(key, Decimal("0")) + tx.net_cash_amount

        return tuple(
            LedgerCash(account_id=acct_id, currency=currency, amount=amount)
            for (acct_id, currency), amount in sorted(amounts.items())
            if amount != 0
        )

    def build_liabilities(self, as_of_date: date, account_id: int | None = None) -> tuple[LedgerLiability, ...]:
        latest: dict[tuple[int | None, str, str, str], object] = {}
        for liability in self.liabilities.list_liabilities(account_id=account_id, through_date=as_of_date):
            key = (liability.account_id, liability.liability_name, liability.liability_type, liability.currency)
            previous = latest.get(key)
            if previous is None or liability.as_of_date >= previous.as_of_date:  # type: ignore[attr-defined]
                latest[key] = liability
        result: list[LedgerLiability] = []
        for liability in latest.values():
            if not liability.is_active:  # type: ignore[attr-defined]
                continue
            result.append(
                LedgerLiability(
                    liability_id=liability.liability_id,  # type: ignore[attr-defined]
                    account_id=liability.account_id,  # type: ignore[attr-defined]
                    liability_name=liability.liability_name,  # type: ignore[attr-defined]
                    liability_type=liability.liability_type,  # type: ignore[attr-defined]
                    currency=liability.currency,  # type: ignore[attr-defined]
                    current_amount=liability.current_amount,  # type: ignore[attr-defined]
                )
            )
        return tuple(sorted(result, key=lambda item: (item.account_id or 0, item.liability_name, item.currency)))

    def build_tax_reserves(self, as_of_date: date, account_id: int | None = None) -> tuple[LedgerTaxReserve, ...]:
        latest: dict[tuple[int | None, int, str, str], object] = {}
        for reserve in self.tax_reserves.list_tax_reserves(account_id=account_id, through_date=as_of_date):
            key = (reserve.account_id, reserve.tax_year, reserve.tax_type, reserve.currency)
            previous = latest.get(key)
            if previous is None or reserve.as_of_date >= previous.as_of_date:  # type: ignore[attr-defined]
                latest[key] = reserve
        result: list[LedgerTaxReserve] = []
        for reserve in latest.values():
            if not reserve.is_active:  # type: ignore[attr-defined]
                continue
            result.append(
                LedgerTaxReserve(
                    tax_reserve_id=reserve.tax_reserve_id,  # type: ignore[attr-defined]
                    account_id=reserve.account_id,  # type: ignore[attr-defined]
                    tax_year=reserve.tax_year,  # type: ignore[attr-defined]
                    tax_type=reserve.tax_type,  # type: ignore[attr-defined]
                    currency=reserve.currency,  # type: ignore[attr-defined]
                    reserved_amount=reserve.reserved_amount,  # type: ignore[attr-defined]
                )
            )
        return tuple(sorted(result, key=lambda item: (item.account_id or 0, item.tax_year, item.tax_type, item.currency)))
