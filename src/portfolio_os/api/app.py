from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from portfolio_os.api.deps import (
    resolve_app_mode,
    resolve_db_path,
    resolve_report_dir,
    resolve_snapshot_dir,
    resolve_upload_limit,
)
from portfolio_os.api.errors import register_error_handlers
from portfolio_os.api.routers import api_router


def create_app(
    db_path: str | Path | None = None,
    app_mode: str | None = None,
    snapshot_dir: str | Path | None = None,
    report_dir: str | Path | None = None,
    upload_limit_bytes: int | None = None,
) -> FastAPI:
    application = FastAPI(
        title="Portfolio OS Frontend API",
        description="Read access plus reconciliation and risk-gated manual operating loop writes over existing Portfolio OS domain services.",
        version="0.3.0",
    )
    application.state.db_path = resolve_db_path(db_path)
    application.state.app_mode = resolve_app_mode(app_mode)
    application.state.snapshot_dir = resolve_snapshot_dir(snapshot_dir)
    application.state.report_dir = resolve_report_dir(report_dir)
    application.state.upload_limit_bytes = resolve_upload_limit(upload_limit_bytes)
    register_error_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
