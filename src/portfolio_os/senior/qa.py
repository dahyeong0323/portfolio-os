from __future__ import annotations

from portfolio_os.db.connection import Database
from portfolio_os.macro.repositories import MacroContextPacketRepository
from portfolio_os.research.repositories import ResearchPacketRepository
from portfolio_os.senior.lint import SeniorMemoLintService
from portfolio_os.senior.models import SeniorMemoQAResult
from portfolio_os.senior.repositories import (
    DecisionCandidateRepository,
    DecisionChangeTriggerRepository,
    NoActionAlternativeRepository,
    OpposingArgumentRepository,
    SeniorMemoInputBundleRepository,
    SeniorMemoQARepository,
    SeniorMemoRepository,
    SeniorMemoSectionRepository,
)

REQUIRED_SECTION_TYPES: tuple[str, ...] = (
    "portfolio_diagnosis",
    "macro_interpretation",
    "cash_liquidity",
    "asset_thesis_status",
    "risk_context",
    "execution_context",
    "no_action_case",
    "opposing_argument",
    "change_triggers",
    "required_risk_validation",
)


class SeniorMemoQAService:
    def __init__(self, db: Database, lint_service: SeniorMemoLintService | None = None) -> None:
        self.db = db
        self.lint_service = lint_service or SeniorMemoLintService()

    def run_qa(self, senior_memo_id: int) -> SeniorMemoQAResult:
        memo = SeniorMemoRepository(self.db).get(senior_memo_id)
        bundle = SeniorMemoInputBundleRepository(self.db).get(memo.input_bundle_id)
        sections = SeniorMemoSectionRepository(self.db).list_sections(senior_memo_id)
        candidates = DecisionCandidateRepository(self.db).list_candidates(senior_memo_id)
        no_actions = NoActionAlternativeRepository(self.db).list_for_memo(senior_memo_id)
        opposing = OpposingArgumentRepository(self.db).list_for_memo(senior_memo_id)
        triggers = DecisionChangeTriggerRepository(self.db).list_for_memo(senior_memo_id)

        section_types = {section.section_type for section in sections}
        missing_sections = tuple(section for section in REQUIRED_SECTION_TYPES if section not in section_types)
        failures: list[str] = []
        warnings: list[str] = []
        invalid_input_count = 0

        if missing_sections:
            failures.append("senior memo is missing required sections")
        if not no_actions:
            failures.append("senior memo requires at least one no-action alternative")
        if not opposing:
            failures.append("senior memo requires at least one opposing argument")
        if not triggers:
            failures.append("senior memo requires at least one decision change trigger")

        if not bundle.research_packet_ids and not bundle.portfolio_only:
            invalid_input_count += 1
            failures.append("input bundle requires research packets unless portfolio_only is true")
        if bundle.portfolio_only and memo.memo_scope != "portfolio":
            invalid_input_count += 1
            failures.append("portfolio_only input bundle can only produce portfolio-scope memos")

        research_repo = ResearchPacketRepository(self.db)
        for packet_id in bundle.research_packet_ids:
            packet = research_repo.get(packet_id)
            if packet.packet_status != "valid" or packet.qa_status != "passed":
                invalid_input_count += 1
                failures.append(f"research packet is not valid/passed: {packet_id}")

        if bundle.macro_context_packet_id is not None:
            macro_packet = MacroContextPacketRepository(self.db).get(bundle.macro_context_packet_id)
            if macro_packet.packet_status != "valid":
                invalid_input_count += 1
                failures.append(f"macro context packet is not valid: {bundle.macro_context_packet_id}")

        forbidden_hits: list[str] = []
        forbidden_hits.extend(self.lint_service.find_forbidden_execution_language(memo.executive_summary))
        for section in sections:
            forbidden_hits.extend(self.lint_service.find_forbidden_execution_language(section.section_text))
        for candidate in candidates:
            forbidden_hits.extend(self.lint_service.find_forbidden_execution_language(candidate.candidate_text))
            forbidden_hits.extend(self.lint_service.find_forbidden_execution_language(candidate.rationale))
        if forbidden_hits:
            failures.append("senior memo contains forbidden execution-authority language")

        if bundle.ledger_status != "reconciled":
            warnings.append("Ledger is not reconciled; no official action candidate can proceed without upstream reconciliation or override flow.")

        for candidate in candidates:
            if candidate.candidate_action_class in {"risk_increasing", "risk_reducing"} and not candidate.risk_validation_required:
                failures.append("trade-related candidate must show Stage 2 risk validation is required")
            if candidate.candidate_action_class == "risk_increasing" and bundle.ledger_status != "reconciled":
                if candidate.candidate_status != "blocked_pending_reconciliation" or candidate.required_next_step != "reconciliation_required" or not candidate.reconciliation_required_first:
                    failures.append("risk-increasing candidate must be blocked pending reconciliation when ledger is not reconciled")
            if candidate.candidate_action_class in {"risk_increasing", "risk_reducing"} and candidate.required_next_step not in {"stage2_create_intent", "stage2_risk_validation", "reconciliation_required"}:
                failures.append("trade-related candidate must point to a Stage 2 or reconciliation next step")

        status = "failed" if failures else "passed"
        return SeniorMemoQAResult(
            senior_memo_qa_id=0,
            senior_memo_id=senior_memo_id,
            qa_status=status,
            required_section_count=len(REQUIRED_SECTION_TYPES) - len(missing_sections),
            missing_required_sections=missing_sections,
            candidate_count=len(candidates),
            no_action_count=len(no_actions),
            opposing_argument_count=len(opposing),
            change_trigger_count=len(triggers),
            invalid_input_count=invalid_input_count,
            forbidden_language_count=len(forbidden_hits),
            failure_reasons=tuple(failures),
            warnings=tuple(warnings),
            created_at=None,
        )

    def run_and_apply(self, senior_memo_id: int) -> SeniorMemoQAResult:
        result = self.run_qa(senior_memo_id)
        saved = SeniorMemoQARepository(self.db).save_result(result)
        SeniorMemoRepository(self.db).update_status(senior_memo_id, "valid" if saved.qa_status == "passed" else "invalid", "passed" if saved.qa_status == "passed" else "failed")
        return saved
