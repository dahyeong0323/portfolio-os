from __future__ import annotations

from typing import Sequence

from portfolio_os.db.connection import Database
from portfolio_os.senior.repositories import (
    DecisionCandidateRepository,
    DecisionChangeTriggerRepository,
    NoActionAlternativeRepository,
    OpposingArgumentRepository,
    SeniorMemoInputBundleRepository,
    SeniorMemoRepository,
    SeniorMemoSectionRepository,
)

CANDIDATE_ACTION_CLASS_BY_TYPE = {
    "create_intent_candidate": "risk_increasing",
    "reduce_risk_candidate": "risk_reducing",
    "correction_review": "correction",
    "no_action": "review_only",
    "review": "review_only",
    "watchlist_update": "review_only",
    "research_needed": "review_only",
}


def classify_candidate_action(candidate_type: str) -> str:
    try:
        return CANDIDATE_ACTION_CLASS_BY_TYPE[candidate_type]
    except KeyError as exc:
        raise ValueError(f"unknown candidate_type: {candidate_type}") from exc


class SeniorMemoService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_memo(self, input_bundle_id: int, memo_title: str, memo_scope: str, executive_summary: str, confidence_level: str = "medium", primary_risk_summary: str | None = None, created_by: str = "human"):
        bundle = SeniorMemoInputBundleRepository(self.db).get(input_bundle_id)
        recommendation_scope = "no_official_action" if bundle.ledger_status != "reconciled" else "candidate_actions_require_risk"
        return SeniorMemoRepository(self.db).create_memo(input_bundle_id, memo_title, bundle.as_of_date, memo_scope, recommendation_scope, executive_summary, confidence_level, primary_risk_summary, True, created_by)

    def add_section(self, senior_memo_id: int, section_type: str, section_title: str, section_text: str, source_refs: Sequence[str] = ()):
        SeniorMemoRepository(self.db).get(senior_memo_id)
        return SeniorMemoSectionRepository(self.db).add_section(senior_memo_id, section_type, section_title, section_text, source_refs)

    def add_candidate(self, senior_memo_id: int, instrument_id: int | None, candidate_type: str, candidate_text: str, rationale: str, required_next_step: str | None = None, priority: str = "medium"):
        memo = SeniorMemoRepository(self.db).get(senior_memo_id)
        bundle = SeniorMemoInputBundleRepository(self.db).get(memo.input_bundle_id)
        action_class = classify_candidate_action(candidate_type)
        risk_validation_required = action_class in {"risk_increasing", "risk_reducing"}
        reconciliation_required_first = action_class == "risk_increasing" and bundle.ledger_status != "reconciled"

        if reconciliation_required_first:
            candidate_status = "blocked_pending_reconciliation"
            final_next_step = "reconciliation_required"
        elif risk_validation_required:
            candidate_status = "blocked_pending_risk_validation"
            final_next_step = required_next_step if required_next_step in {"stage2_create_intent", "stage2_risk_validation"} else "stage2_risk_validation"
        elif action_class == "correction":
            candidate_status = "valid"
            final_next_step = required_next_step if required_next_step else "correction_required"
        else:
            candidate_status = "valid"
            final_next_step = required_next_step if required_next_step else "human_review"

        return DecisionCandidateRepository(self.db).add_candidate(
            senior_memo_id,
            instrument_id,
            candidate_type,
            action_class,
            candidate_text,
            rationale,
            final_next_step,
            candidate_status,
            priority,
            risk_validation_required,
            reconciliation_required_first,
        )

    def add_no_action_alternative(self, senior_memo_id: int, alternative_text: str, why_reasonable: str, opportunity_cost: str | None = None, risk_reduction_benefit: str | None = None, review_trigger: str | None = None):
        SeniorMemoRepository(self.db).get(senior_memo_id)
        return NoActionAlternativeRepository(self.db).add(senior_memo_id, alternative_text, why_reasonable, opportunity_cost, risk_reduction_benefit, review_trigger)

    def add_opposing_argument(self, senior_memo_id: int, argument_text: str, severity: str = "medium", source_refs: Sequence[str] = ()):
        SeniorMemoRepository(self.db).get(senior_memo_id)
        return OpposingArgumentRepository(self.db).add(senior_memo_id, argument_text, severity, source_refs)

    def add_decision_change_trigger(self, senior_memo_id: int, trigger_text: str, trigger_type: str, monitoring_note: str | None = None):
        SeniorMemoRepository(self.db).get(senior_memo_id)
        return DecisionChangeTriggerRepository(self.db).add(senior_memo_id, trigger_text, trigger_type, monitoring_note)

    def archive_memo(self, senior_memo_id: int):
        return SeniorMemoRepository(self.db).archive(senior_memo_id)
