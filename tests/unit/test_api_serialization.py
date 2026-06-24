from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from portfolio_os.api.serialization import serialize_value


@dataclass(frozen=True)
class SerializationExample:
    amount: Decimal
    as_of_date: date
    generated_at: datetime


def test_api_serialization_handles_dataclasses_decimal_date_and_datetime() -> None:
    value = SerializationExample(
        amount=Decimal("12.3400"),
        as_of_date=date(2026, 6, 14),
        generated_at=datetime(2026, 6, 14, 8, 30, tzinfo=timezone.utc),
    )
    assert serialize_value(value) == {
        "amount": "12.3400",
        "as_of_date": "2026-06-14",
        "generated_at": "2026-06-14T08:30:00Z",
    }
