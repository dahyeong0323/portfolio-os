from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from portfolio_os.api.errors import ApiError
from portfolio_os.api.reports import ReportRecord, ReportRegistry
from portfolio_os.api.schemas.reports import (
    ReportCategoryListResponse,
    ReportCategorySchema,
    ReportDetailResponse,
    ReportListItemSchema,
    ReportListResponse,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _registry(request: Request) -> ReportRegistry:
    return ReportRegistry(Path(request.app.state.report_dir))


def _item(record: ReportRecord) -> ReportListItemSchema:
    return ReportListItemSchema(
        report_reference=record.report_reference,
        category=record.category,
        title=record.title,
        format=record.format,
        generated_at=record.generated_at,
        linked_object_type=record.linked_object_type,
        linked_object_id=record.linked_object_id,
        safe_summary=record.safe_summary,
        available_actions=record.available_actions,
        blocked_actions=record.blocked_actions,
    )


@router.get("/categories", response_model=ReportCategoryListResponse)
async def list_report_categories(request: Request) -> ReportCategoryListResponse:
    categories = [ReportCategorySchema.model_validate(item) for item in _registry(request).categories()]
    return ReportCategoryListResponse(categories=categories)


@router.get("", response_model=ReportListResponse)
async def list_reports(
    request: Request,
    category: str | None = None,
    format: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> ReportListResponse:
    count, records = _registry(request).list_reports(
        category=category,
        report_format=format,
        limit=limit,
        offset=offset,
    )
    return ReportListResponse(count=count, reports=[_item(record) for record in records])


@router.get("/{report_reference}", response_model=ReportDetailResponse)
async def get_report(report_reference: str, request: Request) -> ReportDetailResponse:
    record = _registry(request).get_report(report_reference)
    try:
        content = record.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ApiError(404, "report_not_found", "The report was not found.") from exc
    return ReportDetailResponse(
        report_reference=record.report_reference,
        category=record.category,
        title=record.title,
        format=record.format,
        content=content,
        generated_at=record.generated_at,
        linked_object_type=record.linked_object_type,
        linked_object_id=record.linked_object_id,
        available_actions=record.available_actions,
        blocked_actions=record.blocked_actions,
    )


@router.get("/{report_reference}/download")
async def download_report(report_reference: str, request: Request) -> FileResponse:
    record = _registry(request).get_report(report_reference)
    media_type = "text/markdown; charset=utf-8" if record.format == "markdown" else "application/json"
    return FileResponse(record.path, media_type=media_type, filename=record.filename)
