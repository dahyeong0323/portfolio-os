from datetime import datetime

from portfolio_os.api.schemas import ApiSchema


class ReportCategorySchema(ApiSchema):
    category_id: str
    label: str
    description: str
    report_count: int
    supported_formats: list[str]
    latest_generated_at: datetime | None


class ReportCategoryListResponse(ApiSchema):
    categories: list[ReportCategorySchema]


class ReportListItemSchema(ApiSchema):
    report_reference: str
    category: str
    title: str
    format: str
    generated_at: datetime | None
    linked_object_type: str | None
    linked_object_id: str | None
    safe_summary: str | None
    available_actions: list[str]
    blocked_actions: list[str]


class ReportListResponse(ApiSchema):
    count: int
    reports: list[ReportListItemSchema]


class ReportDetailResponse(ApiSchema):
    report_reference: str
    category: str
    title: str
    format: str
    content: str
    generated_at: datetime | None
    linked_object_type: str | None
    linked_object_id: str | None
    available_actions: list[str]
    blocked_actions: list[str]
