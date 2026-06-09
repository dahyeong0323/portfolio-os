from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

SeniorMemoStatus = Literal["draft", "valid", "invalid", "archived"]
MemoScope = Literal["portfolio", "asset", "multi_asset"]
MemoRecommendationScope = Literal["review_only", "candidate_actions_require_risk", "no_official_action"]
CandidateType = Literal["no_action", "review", "create_intent_candidate", "reduce_risk_candidate", "watchlist_update", "research_needed", "correction_review"]
CandidateActionClass = Literal["review_only", "risk_increasing", "risk_reducing", "correction"]
RequiredNextStep = Literal["none", "human_review", "stage2_create_intent", "stage2_risk_validation", "additional_research", "reconciliation_required", "correction_required"]
CandidateStatus = Literal["draft", "valid", "blocked_pending_reconciliation", "blocked_pending_risk_validation", "archived"]
SeniorMemoQAStatus = Literal["not_run", "passed", "failed"]


@dataclass(frozen=True)
class SeniorMemoInputBundle:
    input_bundle_id: int
    as_of_date: date
    ledger_status: str
    latest_reconciliation_id: int | None
    portfolio_only: bool
    research_packet_ids: tuple[int, ...]
    macro_context_packet_id: int | None
    risk_validation_ids: tuple[int, ...]
    order_ticket_ids: tuple[int, ...]
    manual_execution_ids: tuple[int, ...]
    override_ticket_ids: tuple[int, ...]
    decision_journal_ids: tuple[int, ...]
    input_digest: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class SeniorMemo:
    senior_memo_id: int
    input_bundle_id: int
    memo_title: str
    as_of_date: date
    memo_status: SeniorMemoStatus
    memo_scope: MemoScope
    memo_recommendation_scope: MemoRecommendationScope
    executive_summary: str
    confidence_level: str
    primary_risk_summary: str | None
    no_action_is_acceptable: bool
    qa_status: SeniorMemoQAStatus
    created_by: str
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class SeniorMemoSection:
    section_id: int
    senior_memo_id: int
    section_type: str
    section_title: str
    section_text: str
    source_refs: tuple[str, ...]
    created_at: datetime | None


@dataclass(frozen=True)
class DecisionCandidate:
    decision_candidate_id: int
    senior_memo_id: int
    instrument_id: int | None
    candidate_type: CandidateType
    candidate_action_class: CandidateActionClass
    candidate_text: str
    rationale: str
    required_next_step: RequiredNextStep
    candidate_status: CandidateStatus
    priority: str
    risk_validation_required: bool
    reconciliation_required_first: bool
    created_at: datetime | None


@dataclass(frozen=True)
class NoActionAlternative:
    no_action_id: int
    senior_memo_id: int
    alternative_text: str
    why_reasonable: str
    opportunity_cost: str | None
    risk_reduction_benefit: str | None
    review_trigger: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class OpposingArgument:
    opposing_argument_id: int
    senior_memo_id: int
    argument_text: str
    severity: str
    source_refs: tuple[str, ...]
    created_at: datetime | None


@dataclass(frozen=True)
class DecisionChangeTrigger:
    change_trigger_id: int
    senior_memo_id: int
    trigger_text: str
    trigger_type: str
    monitoring_note: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class SeniorMemoQAResult:
    senior_memo_qa_id: int
    senior_memo_id: int
    qa_status: Literal["passed", "failed"]
    required_section_count: int
    missing_required_sections: tuple[str, ...]
    candidate_count: int
    no_action_count: int
    opposing_argument_count: int
    change_trigger_count: int
    invalid_input_count: int
    forbidden_language_count: int
    failure_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at: datetime | None
