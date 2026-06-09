from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

ResearchPacketStatus = Literal["draft", "valid", "invalid", "archived"]
ResearchQAStatus = Literal["not_run", "passed", "failed"]
FactCategory = Literal["bull", "bear", "neutral"]
ThesisRelation = Literal["supporting", "challenging", "neutral", "unknown"]
SourceType = Literal["filing", "earnings", "news", "price_data", "company_website", "analyst_note", "macro_data", "manual_note", "other"]


@dataclass(frozen=True)
class AssetThesis:
    thesis_id: int
    instrument_id: int
    thesis_title: str
    thesis_text: str
    invalidation_triggers: tuple[str, ...]
    watch_questions: tuple[str, ...]
    status: str
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class ResearchSource:
    source_id: int
    source_type: SourceType
    title: str
    publisher: str | None
    url: str | None
    local_path: str | None
    published_at: datetime | None
    retrieved_at: datetime | None
    source_hash: str | None
    freshness_status: str
    reliability_note: str | None


@dataclass(frozen=True)
class ResearchPacket:
    research_packet_id: int
    instrument_id: int
    thesis_id: int | None
    packet_version: str
    as_of_date: date
    packet_status: ResearchPacketStatus
    summary_text: str | None
    missing_data_summary: str | None
    qa_status: ResearchQAStatus
    created_by: str
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class ResearchFact:
    fact_id: int
    research_packet_id: int
    source_id: int
    fact_category: FactCategory
    thesis_relation: ThesisRelation
    fact_type: str
    fact_text: str
    numeric_value: Decimal | None
    numeric_unit: str | None
    observed_at: datetime | None
    created_at: datetime | None


@dataclass(frozen=True)
class ResearchMissingData:
    missing_data_id: int
    research_packet_id: int
    data_question: str
    importance: str
    attempted_sources: tuple[str, ...]
    impact_note: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class ResearchQAResult:
    research_qa_id: int
    research_packet_id: int
    qa_status: Literal["passed", "failed"]
    bull_fact_count: int
    bear_fact_count: int
    neutral_fact_count: int
    supporting_fact_count: int
    challenging_fact_count: int
    missing_data_count: int
    source_count: int
    forbidden_language_count: int
    failure_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at: datetime | None
