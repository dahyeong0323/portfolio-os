from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request

from portfolio_os.api.deps import get_database
from portfolio_os.api.errors import ApiError
from portfolio_os.api.reports import ReportRegistry
from portfolio_os.api.schemas.context_explorer import (
    CONTEXT_BLOCKED_ACTIONS,
    READ_ONLY_ACTIONS,
    GovernanceEventListResponse,
    GovernanceEventSchema,
    GovernanceOverviewResponse,
    MacroDetailResponse,
    MacroItemSchema,
    MacroListResponse,
    ResearchDetailResponse,
    ResearchItemSchema,
    ResearchListResponse,
    SeniorMemoDetailResponse,
    SeniorMemoItemSchema,
    SeniorMemoListResponse,
)
from portfolio_os.context.repositories import ContextPackageRepository
from portfolio_os.db import Database
from portfolio_os.governance.repositories import CanaryRepository, SystemHealthRepository, audit_event_from_row
from portfolio_os.macro.repositories import MacroContextPacketRepository, MacroRegimeRepository, macro_packet_from_row
from portfolio_os.research.repositories import (
    AssetThesisRepository,
    ResearchFactRepository,
    ResearchMissingDataRepository,
    ResearchPacketRepository,
    ResearchQARepository,
    ResearchSourceRepository,
    packet_from_row,
)
from portfolio_os.senior.repositories import (
    DecisionCandidateRepository,
    NoActionAlternativeRepository,
    OpposingArgumentRepository,
    SeniorMemoInputBundleRepository,
    SeniorMemoRepository,
    SeniorMemoSectionRepository,
    memo_from_row,
)

router = APIRouter(tags=["context-explorer"])


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def _report_map(request: Request, category: str) -> dict[str, str]:
    _count, reports = ReportRegistry(Path(request.app.state.report_dir)).list_reports(category=category, limit=200)
    return {
        str(report.linked_object_id): report.report_reference
        for report in reports
        if report.linked_object_id is not None
    }


def _report_refs(request: Request, category: str, object_id: int | None = None) -> list[str]:
    _count, reports = ReportRegistry(Path(request.app.state.report_dir)).list_reports(category=category, limit=200)
    return [
        report.report_reference
        for report in reports
        if object_id is None or report.linked_object_id == str(object_id)
    ]


def _instrument_label(db: Database, instrument_id: int | None) -> str | None:
    if instrument_id is None:
        return None
    row = db.fetch_one("SELECT symbol, instrument_name FROM instruments WHERE instrument_id = ?", (instrument_id,))
    if row is None:
        return f"instrument #{instrument_id}"
    return f"{row['symbol']} - {row['instrument_name']}"


@router.get("/research", response_model=ResearchListResponse)
async def list_research(request: Request, db: Database = Depends(get_database)) -> ResearchListResponse:
    report_refs = _report_map(request, "research")
    rows = db.fetch_all("SELECT * FROM research_packets ORDER BY research_packet_id DESC")
    items: list[ResearchItemSchema] = []
    for row in rows:
        packet = packet_from_row(row)
        thesis = AssetThesisRepository(db).get(packet.thesis_id) if packet.thesis_id else None
        facts = ResearchFactRepository(db).list_facts(packet.research_packet_id)
        anti_present = any(fact.thesis_relation in {"challenging", "bear"} or fact.fact_category == "bear" for fact in facts)
        items.append(
            ResearchItemSchema(
                research_id=packet.research_packet_id,
                title=f"Research Packet #{packet.research_packet_id}",
                subject=packet.summary_text,
                instrument=_instrument_label(db, packet.instrument_id),
                thesis=thesis.thesis_title if thesis else None,
                status=packet.packet_status,
                created_at=packet.created_at,
                updated_at=packet.updated_at,
                linked_report_reference=report_refs.get(str(packet.research_packet_id)),
                anti_thesis_present=anti_present,
                available_actions=list(READ_ONLY_ACTIONS),
                blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
            )
        )
    return ResearchListResponse(count=len(items), items=items)


@router.get("/research/{research_id}", response_model=ResearchDetailResponse)
async def get_research(research_id: int, request: Request, db: Database = Depends(get_database)) -> ResearchDetailResponse:
    try:
        packet = ResearchPacketRepository(db).get(research_id)
    except ValueError as exc:
        raise ApiError(404, "research_not_found", "The research record was not found.") from exc
    thesis = AssetThesisRepository(db).get(packet.thesis_id) if packet.thesis_id else None
    facts = ResearchFactRepository(db).list_facts(research_id)
    missing = ResearchMissingDataRepository(db).list_missing_data(research_id)
    qa = ResearchQARepository(db).get_latest_result(research_id)
    source_repo = ResearchSourceRepository(db)
    sources = []
    for source_id in sorted({fact.source_id for fact in facts}):
        try:
            source = source_repo.get(source_id)
        except ValueError:
            continue
        sources.append({"source_id": source.source_id, "title": source.title, "source_type": source.source_type, "publisher": source.publisher, "freshness_status": source.freshness_status})
    anti_facts = [fact for fact in facts if fact.thesis_relation in {"challenging", "bear"} or fact.fact_category == "bear"]
    return ResearchDetailResponse(
        metadata={**asdict(packet), "instrument": _instrument_label(db, packet.instrument_id)},
        thesis=asdict(thesis) if thesis else None,
        anti_thesis={"present": bool(anti_facts), "facts": [asdict(fact) for fact in anti_facts[:10]]},
        sources=sources,
        evidence_summary={"fact_count": len(facts), "missing_data_count": len(missing), "qa": _plain(qa)},
        linked_reports=_report_refs(request, "research", research_id),
        read_only_explanation="Research context is read-only evidence. It is not order authority and must pass through Risk Engine and ticket approval before any trade.",
        available_actions=list(READ_ONLY_ACTIONS),
        blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
    )


@router.get("/macro", response_model=MacroListResponse)
async def list_macro(request: Request, db: Database = Depends(get_database)) -> MacroListResponse:
    report_refs = _report_map(request, "macro")
    rows = db.fetch_all("SELECT * FROM macro_context_packets ORDER BY macro_context_packet_id DESC")
    items: list[MacroItemSchema] = []
    regime_repo = MacroRegimeRepository(db)
    for row in rows:
        packet = macro_packet_from_row(row)
        regime = None
        if packet.macro_regime_id:
            try:
                regime = regime_repo.get(packet.macro_regime_id)
            except ValueError:
                regime = None
        tags = [packet.risk_on_exposure, packet.liquidity_sensitivity, packet.correlation_stress, packet.defensive_buffer]
        items.append(
            MacroItemSchema(
                macro_id=packet.macro_context_packet_id,
                title=f"Macro Context #{packet.macro_context_packet_id}",
                regime=regime.regime if regime else None,
                scenario=packet.summary_text,
                tags=[tag for tag in tags if tag],
                created_at=packet.created_at,
                linked_report_reference=report_refs.get(str(packet.macro_context_packet_id)),
                available_actions=list(READ_ONLY_ACTIONS),
                blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
            )
        )
    return MacroListResponse(count=len(items), items=items)


@router.get("/macro/{macro_id}", response_model=MacroDetailResponse)
async def get_macro(macro_id: int, request: Request, db: Database = Depends(get_database)) -> MacroDetailResponse:
    try:
        packet = MacroContextPacketRepository(db).get(macro_id)
    except ValueError as exc:
        raise ApiError(404, "macro_context_not_found", "The macro context record was not found.") from exc
    regime = None
    if packet.macro_regime_id:
        try:
            regime = MacroRegimeRepository(db).get(packet.macro_regime_id)
        except ValueError:
            regime = None
    tags = [packet.risk_on_exposure, packet.liquidity_sensitivity, packet.btc_related_exposure, packet.nasdaq_growth_exposure, packet.correlation_stress, packet.defensive_buffer]
    return MacroDetailResponse(
        metadata=asdict(packet),
        regime=asdict(regime) if regime else None,
        scenario={"summary_text": packet.summary_text, "unknowns": list(packet.unknowns)},
        tags=[tag for tag in tags if tag],
        linked_reports=_report_refs(request, "macro", macro_id),
        read_only_explanation="Macro context is scenario context only. It is not a timing signal, allocation command, broker instruction, or order authority.",
        available_actions=list(READ_ONLY_ACTIONS),
        blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
    )


@router.get("/senior-memos", response_model=SeniorMemoListResponse)
async def list_senior_memos(request: Request, db: Database = Depends(get_database)) -> SeniorMemoListResponse:
    report_refs = _report_map(request, "senior_memo")
    rows = db.fetch_all("SELECT * FROM senior_memos ORDER BY senior_memo_id DESC")
    memos: list[SeniorMemoItemSchema] = []
    for row in rows:
        memo = memo_from_row(row)
        bundle = SeniorMemoInputBundleRepository(db).get(memo.input_bundle_id)
        memos.append(
            SeniorMemoItemSchema(
                memo_id=memo.senior_memo_id,
                title=memo.memo_title,
                ticket_id=bundle.order_ticket_ids[0] if bundle.order_ticket_ids else None,
                risk_validation_id=bundle.risk_validation_ids[0] if bundle.risk_validation_ids else None,
                recommendation_summary=f"Context only: {memo.executive_summary}",
                created_at=memo.created_at,
                linked_report_reference=report_refs.get(str(memo.senior_memo_id)),
                available_actions=list(READ_ONLY_ACTIONS),
                blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
            )
        )
    return SeniorMemoListResponse(count=len(memos), memos=memos)


@router.get("/senior-memos/{memo_id}", response_model=SeniorMemoDetailResponse)
async def get_senior_memo(memo_id: int, request: Request, db: Database = Depends(get_database)) -> SeniorMemoDetailResponse:
    try:
        memo = SeniorMemoRepository(db).get(memo_id)
    except ValueError as exc:
        raise ApiError(404, "senior_memo_not_found", "The senior memo was not found.") from exc
    bundle = SeniorMemoInputBundleRepository(db).get(memo.input_bundle_id)
    return SeniorMemoDetailResponse(
        metadata=asdict(memo),
        input_bundle=asdict(bundle),
        sections=[asdict(item) for item in SeniorMemoSectionRepository(db).list_sections(memo_id)],
        decision_candidates=[asdict(item) for item in DecisionCandidateRepository(db).list_candidates(memo_id)],
        no_action_alternatives=[asdict(item) for item in NoActionAlternativeRepository(db).list_for_memo(memo_id)],
        opposing_arguments=[asdict(item) for item in OpposingArgumentRepository(db).list_for_memo(memo_id)],
        linked_reports=_report_refs(request, "senior_memo", memo_id),
        read_only_explanation="Senior Memo is advisory context only. Official order ticket creation and approval remain available only through the Stage 2 Risk Engine path.",
        available_actions=list(READ_ONLY_ACTIONS),
        blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
    )


@router.get("/governance", response_model=GovernanceOverviewResponse)
async def get_governance_overview(request: Request, db: Database = Depends(get_database)) -> GovernanceOverviewResponse:
    latest_package = db.fetch_one("SELECT * FROM context_packages ORDER BY context_package_id DESC LIMIT 1")
    package_payload = None
    stale_warnings: list[str] = []
    if latest_package:
        package = ContextPackageRepository(db).get(latest_package["context_package_id"])
        budget = ContextPackageRepository(db).latest_budget(package.context_package_id)
        package_payload = {"package": asdict(package), "budget": _plain(budget)}
        if package.package_status not in {"validated", "complete"}:
            stale_warnings.append(f"Context package status is {package.package_status}.")
        if package.budget_status not in {"ok", "within_budget"}:
            stale_warnings.append(f"Context budget status is {package.budget_status}.")
    canary = CanaryRepository(db).get_latest_run()
    health = SystemHealthRepository(db).latest()
    if health and health.warning_count:
        stale_warnings.append(f"System health has {health.warning_count} warning(s).")
    if health and health.failure_count:
        stale_warnings.append(f"System health has {health.failure_count} failure(s).")
    return GovernanceOverviewResponse(
        context_package_status=package_payload,
        canary=_plain(canary),
        health=_plain(health),
        stale_context_warnings=stale_warnings,
        governance_report_references=_report_refs(request, "governance"),
        canary_report_references=_report_refs(request, "canary"),
        health_report_references=_report_refs(request, "health"),
        context_report_references=_report_refs(request, "context_package"),
        available_actions=list(READ_ONLY_ACTIONS),
        blocked_actions=list(CONTEXT_BLOCKED_ACTIONS),
    )


@router.get("/governance/events", response_model=GovernanceEventListResponse)
async def list_governance_events(db: Database = Depends(get_database)) -> GovernanceEventListResponse:
    rows = db.fetch_all("SELECT * FROM governance_audit_events ORDER BY governance_audit_event_id DESC LIMIT 100")
    events = [audit_event_from_row(row) for row in rows]
    return GovernanceEventListResponse(
        count=len(events),
        events=[
            GovernanceEventSchema(
                event_id=event.governance_audit_event_id,
                event_type=event.event_type,
                event_scope=event.event_scope,
                severity=event.severity,
                related_table=event.related_table,
                related_id=event.related_id,
                event_summary=event.event_summary,
                created_at=event.created_at,
            )
            for event in events
        ],
    )
