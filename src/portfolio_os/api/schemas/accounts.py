from datetime import date

from portfolio_os.api.schemas import ApiSchema


class AccountSchema(ApiSchema):
    account_id: int
    account_name: str
    institution_name: str
    account_type: str
    base_currency: str
    account_number_masked: str | None
    is_active: bool
    opened_date: date | None
    closed_date: date | None
    notes: str | None


class AccountListResponse(ApiSchema):
    count: int
    active_count: int
    inactive_count: int
    accounts: list[AccountSchema]
