from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from portfolio_os.serialization import loads_json, to_jsonable
from portfolio_os.validators import date_from_text, datetime_from_text, decimal_from_text


def serialize_value(value: Any) -> Any:
    return to_jsonable(value)


def parse_decimal(value: str | None, field_name: str, *, allow_none: bool = False) -> Decimal | None:
    return decimal_from_text(value, field_name, allow_none=allow_none)


def parse_date(value: str | None) -> date | None:
    return date_from_text(value)


def parse_datetime(value: str | None) -> datetime | None:
    return datetime_from_text(value) if value else None


def parse_json_list(value: str, field_name: str) -> list[Any]:
    parsed = loads_json(value)
    if not isinstance(parsed, list):
        raise ValueError(f"stored reconciliation field is not a list: {field_name}")
    return parsed
