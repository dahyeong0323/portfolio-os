from typing import Literal

from portfolio_os.api.schemas import ApiSchema


class MigrationStatusSchema(ApiSchema):
    expected_count: int
    applied_count: int
    latest_expected_version: int | None
    latest_applied_version: int | None
    ready: bool


class HealthResponse(ApiSchema):
    status: Literal["ok", "degraded"]
    api_status: Literal["ok"] = "ok"
    database_reachable: bool
    database_ready: bool
    app_mode: str
    migrations: MigrationStatusSchema
