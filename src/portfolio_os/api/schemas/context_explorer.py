from datetime import date, datetime
from typing import Any

from portfolio_os.api.schemas import ApiSchema


READ_ONLY_ACTIONS = ["view", "open_report"]
CONTEXT_BLOCKED_ACTIONS = ["create_order", "approve", "execute", "broker_write"]


class ResearchItemSchema(ApiSchema):
    research_id: int | None = None
    report_reference: str | None = None
    title: str
    subject: str | None = None
    instrument: str | None = None
    thesis: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    linked_report_reference: str | None = None
    anti_thesis_present: bool | None = None
    available_actions: list[str]
    blocked_actions: list[str]


class ResearchListResponse(ApiSchema):
    count: int
    items: list[ResearchItemSchema]


class ResearchDetailResponse(ApiSchema):
    metadata: dict[str, Any]
    thesis: dict[str, Any] | None = None
    anti_thesis: dict[str, Any] | None = None
    sources: list[dict[str, Any]]
    evidence_summary: dict[str, Any]
    linked_reports: list[str]
    read_only_explanation: str
    available_actions: list[str]
    blocked_actions: list[str]


class MacroItemSchema(ApiSchema):
    macro_id: int | None = None
    report_reference: str | None = None
    title: str
    regime: str | None = None
    scenario: str | None = None
    tags: list[str]
    created_at: datetime | None = None
    linked_report_reference: str | None = None
    available_actions: list[str]
    blocked_actions: list[str]


class MacroListResponse(ApiSchema):
    count: int
    items: list[MacroItemSchema]


class MacroDetailResponse(ApiSchema):
    metadata: dict[str, Any]
    regime: dict[str, Any] | None = None
    scenario: dict[str, Any]
    tags: list[str]
    linked_reports: list[str]
    read_only_explanation: str
    available_actions: list[str]
    blocked_actions: list[str]


class SeniorMemoItemSchema(ApiSchema):
    memo_id: int | None = None
    report_reference: str | None = None
    title: str
    linked_intent_id: int | None = None
    ticket_id: int | None = None
    risk_validation_id: int | None = None
    recommendation_summary: str | None = None
    created_at: datetime | None = None
    linked_report_reference: str | None = None
    available_actions: list[str]
    blocked_actions: list[str]


class SeniorMemoListResponse(ApiSchema):
    count: int
    memos: list[SeniorMemoItemSchema]


class SeniorMemoDetailResponse(ApiSchema):
    metadata: dict[str, Any]
    input_bundle: dict[str, Any] | None = None
    sections: list[dict[str, Any]]
    decision_candidates: list[dict[str, Any]]
    no_action_alternatives: list[dict[str, Any]]
    opposing_arguments: list[dict[str, Any]]
    linked_reports: list[str]
    read_only_explanation: str
    available_actions: list[str]
    blocked_actions: list[str]


class GovernanceOverviewResponse(ApiSchema):
    context_package_status: dict[str, Any] | None = None
    canary: dict[str, Any] | None = None
    health: dict[str, Any] | None = None
    stale_context_warnings: list[str]
    governance_report_references: list[str]
    canary_report_references: list[str]
    health_report_references: list[str]
    context_report_references: list[str]
    available_actions: list[str]
    blocked_actions: list[str]


class GovernanceEventSchema(ApiSchema):
    event_id: int
    event_type: str
    event_scope: str
    severity: str
    related_table: str | None = None
    related_id: int | None = None
    event_summary: str
    created_at: datetime | None = None


class GovernanceEventListResponse(ApiSchema):
    count: int
    events: list[GovernanceEventSchema]
