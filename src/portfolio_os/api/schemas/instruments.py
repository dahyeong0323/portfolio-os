from portfolio_os.api.schemas import ApiSchema


class InstrumentSchema(ApiSchema):
    instrument_id: int
    symbol: str
    instrument_name: str
    instrument_type: str
    exchange: str | None
    isin: str | None
    currency: str
    country: str | None
    is_fractional_allowed: bool
    quantity_precision: int
    price_precision: int
    is_active: bool
    notes: str | None


class InstrumentListResponse(ApiSchema):
    count: int
    active_count: int
    inactive_count: int
    instruments: list[InstrumentSchema]
