from __future__ import annotations

import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from portfolio_os.models import (
    ExternalAccountSnapshot,
    ExternalCash,
    ExternalLiability,
    ExternalPosition,
    ExternalTaxReserve,
    SnapshotSource,
)
from portfolio_os.repositories import InstrumentRepository
from portfolio_os.serialization import to_jsonable
from portfolio_os.validators import datetime_from_text, datetime_to_text, ensure_decimal, utc_now, validate_external_snapshot


class CSVImportError(Exception):
    pass


class AccountSnapshotCSVImporter:
    def __init__(self, instrument_repository: InstrumentRepository | None = None) -> None:
        self.instrument_repository = instrument_repository

    def parse_positions_csv(self, file_path: Path, account_id: int, as_of_date: date) -> tuple[ExternalPosition, ...]:
        del as_of_date
        rows = self._read_rows(file_path)
        positions: list[ExternalPosition] = []
        for index, row in enumerate(rows, start=2):
            symbol = self._required(row, "symbol", index)
            currency = self._required(row, "currency", index)
            quantity = ensure_decimal(self._required(row, "quantity", index), "quantity")
            exchange = self._optional(row, "exchange")
            instrument_id_text = self._optional(row, "instrument_id")
            instrument_id, match_status, match_error = self._resolve_instrument(symbol, currency, exchange, instrument_id_text)
            positions.append(
                ExternalPosition(
                    account_id=account_id,
                    symbol=symbol,
                    currency=currency,
                    quantity=quantity,
                    exchange=exchange,
                    instrument_id=instrument_id,
                    match_status=match_status,
                    match_error=match_error,
                )
            )
        return tuple(positions)

    def parse_cash_csv(self, file_path: Path, account_id: int, as_of_date: date) -> tuple[ExternalCash, ...]:
        del as_of_date
        return tuple(
            ExternalCash(
                account_id=account_id,
                currency=self._required(row, "currency", index),
                amount=ensure_decimal(self._required(row, "amount", index), "amount"),
            )
            for index, row in enumerate(self._read_rows(file_path), start=2)
        )

    def parse_liabilities_csv(self, file_path: Path, as_of_date: date) -> tuple[ExternalLiability, ...]:
        del as_of_date
        liabilities: list[ExternalLiability] = []
        for index, row in enumerate(self._read_rows(file_path), start=2):
            account_id_text = self._optional(row, "account_id")
            liabilities.append(
                ExternalLiability(
                    account_id=int(account_id_text) if account_id_text else None,
                    liability_name=self._required(row, "liability_name", index),
                    liability_type=self._optional(row, "liability_type"),
                    currency=self._required(row, "currency", index),
                    current_amount=ensure_decimal(self._required(row, "current_amount", index), "current_amount"),
                )
            )
        return tuple(liabilities)

    def parse_tax_reserves_csv(self, file_path: Path, as_of_date: date) -> tuple[ExternalTaxReserve, ...]:
        del as_of_date
        reserves: list[ExternalTaxReserve] = []
        for index, row in enumerate(self._read_rows(file_path), start=2):
            account_id_text = self._optional(row, "account_id")
            reserves.append(
                ExternalTaxReserve(
                    account_id=int(account_id_text) if account_id_text else None,
                    tax_year=int(self._required(row, "tax_year", index)),
                    tax_type=self._required(row, "tax_type", index),
                    currency=self._required(row, "currency", index),
                    reserved_amount=ensure_decimal(self._required(row, "reserved_amount", index), "reserved_amount"),
                )
            )
        return tuple(reserves)

    def build_external_snapshot(
        self,
        as_of_date: date,
        source: SnapshotSource,
        positions: Sequence[ExternalPosition],
        cash: Sequence[ExternalCash],
        liabilities: Sequence[ExternalLiability],
        tax_reserves: Sequence[ExternalTaxReserve],
    ) -> ExternalAccountSnapshot:
        snapshot = ExternalAccountSnapshot(
            as_of_date=as_of_date,
            source=source,
            positions=tuple(positions),
            cash=tuple(cash),
            liabilities=tuple(liabilities),
            tax_reserves=tuple(tax_reserves),
            received_at=utc_now(),
        )
        validate_external_snapshot(snapshot)
        return snapshot

    def _resolve_instrument(self, symbol: str, currency: str, exchange: str | None, instrument_id_text: str | None) -> tuple[int | None, str, str | None]:
        if self.instrument_repository is None:
            return None, "missing", "instrument repository unavailable during import"
        if instrument_id_text:
            instrument = self.instrument_repository.get_instrument(int(instrument_id_text))
            if instrument is None:
                return None, "invalid", f"instrument_id not found: {instrument_id_text}"
            if instrument.symbol != symbol or instrument.currency != currency or (exchange and instrument.exchange != exchange):
                return None, "invalid", f"instrument_id {instrument_id_text} does not match symbol/currency/exchange"
            return instrument.instrument_id, "matched", None
        matches = self.instrument_repository.find_by_symbol(symbol=symbol, currency=currency, exchange=exchange)
        if len(matches) == 1:
            return matches[0].instrument_id, "matched", None
        if len(matches) == 0:
            return None, "missing", f"no instrument match for {symbol}/{currency}/{exchange or '*'}"
        return None, "ambiguous", f"multiple instrument matches for {symbol}/{currency}/{exchange or '*'}"

    def _read_rows(self, file_path: Path) -> list[dict[str, str]]:
        try:
            with Path(file_path).open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        except OSError as exc:
            raise CSVImportError(str(exc)) from exc

    def _required(self, row: dict[str, str], column: str, row_number: int) -> str:
        value = row.get(column)
        if value is None or not str(value).strip():
            raise CSVImportError(f"missing {column} at row {row_number}")
        return str(value).strip()

    def _optional(self, row: dict[str, str], column: str) -> str | None:
        value = row.get(column)
        if value is None or not str(value).strip():
            return None
        return str(value).strip()


def write_external_snapshot(snapshot: ExternalAccountSnapshot, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime_to_text(snapshot.received_at).replace(":", "").replace("-", "")
    output_path = output_dir / f"external_snapshot_{snapshot.as_of_date.isoformat()}_{timestamp}.json"
    payload = {"schema": "portfolio_os.external_snapshot.v1", "snapshot": to_jsonable(snapshot)}
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def load_external_snapshot(path: Path) -> ExternalAccountSnapshot:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    data = payload["snapshot"]
    return ExternalAccountSnapshot(
        as_of_date=date.fromisoformat(data["as_of_date"]),
        source=data["source"],
        positions=tuple(
            ExternalPosition(
                account_id=item["account_id"],
                symbol=item["symbol"],
                currency=item["currency"],
                quantity=Decimal(item["quantity"]),
                exchange=item.get("exchange"),
                instrument_id=item.get("instrument_id"),
                match_status=item.get("match_status", "matched"),
                match_error=item.get("match_error"),
            )
            for item in data["positions"]
        ),
        cash=tuple(ExternalCash(account_id=item["account_id"], currency=item["currency"], amount=Decimal(item["amount"])) for item in data["cash"]),
        liabilities=tuple(
            ExternalLiability(
                account_id=item.get("account_id"),
                liability_name=item["liability_name"],
                liability_type=item.get("liability_type"),
                currency=item["currency"],
                current_amount=Decimal(item["current_amount"]),
            )
            for item in data["liabilities"]
        ),
        tax_reserves=tuple(
            ExternalTaxReserve(
                account_id=item.get("account_id"),
                tax_year=item["tax_year"],
                tax_type=item["tax_type"],
                currency=item["currency"],
                reserved_amount=Decimal(item["reserved_amount"]),
            )
            for item in data["tax_reserves"]
        ),
        received_at=datetime_from_text(data["received_at"]),
    )
