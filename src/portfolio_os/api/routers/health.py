from fastapi import APIRouter, Request

from portfolio_os.api.deps import inspect_database
from portfolio_os.api.schemas.health import HealthResponse, MigrationStatusSchema

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    database = inspect_database(request.app.state.db_path)
    return HealthResponse(
        status="ok" if database.ready else "degraded",
        database_reachable=database.reachable,
        database_ready=database.ready,
        app_mode=request.app.state.app_mode,
        migrations=MigrationStatusSchema.model_validate(database.migrations),
    )
