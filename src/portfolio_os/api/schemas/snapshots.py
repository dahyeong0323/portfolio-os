from datetime import date, datetime

from portfolio_os.api.schemas import ApiSchema


class ExternalSnapshotCountsSchema(ApiSchema):
    positions: int
    cash: int
    liabilities: int
    tax_reserves: int


class ExternalSnapshotImportResponse(ApiSchema):
    artifact_id: str
    account_id: int
    source: str
    as_of_date: date
    status: str
    counts: ExternalSnapshotCountsSchema
    warnings: list[str]
    imported_at: datetime
