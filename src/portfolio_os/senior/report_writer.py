from __future__ import annotations

from pathlib import Path

from portfolio_os.db.connection import Database
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
from portfolio_os.serialization import dumps_json


class SeniorMemoReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, senior_memo_id: int) -> dict:
        memo = SeniorMemoRepository(self.db).get(senior_memo_id)
        return {
            "memo": memo,
            "input_bundle": SeniorMemoInputBundleRepository(self.db).get(memo.input_bundle_id),
            "sections": SeniorMemoSectionRepository(self.db).list_sections(senior_memo_id),
            "decision_candidates": DecisionCandidateRepository(self.db).list_candidates(senior_memo_id),
            "no_action_alternatives": NoActionAlternativeRepository(self.db).list_for_memo(senior_memo_id),
            "opposing_arguments": OpposingArgumentRepository(self.db).list_for_memo(senior_memo_id),
            "decision_change_triggers": DecisionChangeTriggerRepository(self.db).list_for_memo(senior_memo_id),
            "qa": SeniorMemoQARepository(self.db).get_latest_result(senior_memo_id),
        }

    def write_markdown_report(self, senior_memo_id: int, output_path: Path) -> Path:
        payload = self._payload(senior_memo_id)
        memo = payload["memo"]
        bundle = payload["input_bundle"]
        sections = payload["sections"]
        candidates = payload["decision_candidates"]
        no_actions = payload["no_action_alternatives"]
        opposing = payload["opposing_arguments"]
        triggers = payload["decision_change_triggers"]
        qa = payload["qa"]

        lines = [
            f"# Senior Decision Memo {memo.senior_memo_id}",
            "",
            "This memo is not an order ticket.",
            "This memo is not a risk validation.",
            "This memo is not execution authorization.",
            "Any candidate action must go through the Stage 2 Risk Engine and ticket workflow.",
            "",
            "## Memo",
            f"- Title: {memo.memo_title}",
            f"- As of date: {memo.as_of_date}",
            f"- Memo status: {memo.memo_status}",
            f"- QA status: {memo.qa_status}",
            f"- Ledger status: {bundle.ledger_status}",
            f"- Portfolio only: {'yes' if bundle.portfolio_only else 'no'}",
            f"- Research packets: {', '.join(str(item) for item in bundle.research_packet_ids) or 'none'}",
            f"- Macro context packet: {bundle.macro_context_packet_id or 'none'}",
            "",
            "## Executive Summary",
            memo.executive_summary,
            "",
            "## Sections",
        ]
        for section in sections:
            lines.extend([f"### {section.section_title}", f"- Type: {section.section_type}", section.section_text, ""])

        lines.append("## Decision Candidates")
        if not candidates:
            lines.append("- none")
        for candidate in candidates:
            lines.extend(
                [
                    f"- Candidate {candidate.decision_candidate_id}: {candidate.candidate_text}",
                    f"  - candidate_status: {candidate.candidate_status}",
                    f"  - required_next_step: {candidate.required_next_step}",
                    f"  - Stage 2 risk validation still required: {'yes' if candidate.risk_validation_required else 'no'}",
                    f"  - Reconciliation required first: {'yes' if candidate.reconciliation_required_first else 'no'}",
                    f"  - action_class: {candidate.candidate_action_class}",
                ]
            )

        lines.extend(["", "## No-Action Alternatives"])
        for item in no_actions:
            lines.append(f"- {item.alternative_text} Reason: {item.why_reasonable}")
        lines.extend(["", "## Opposing Arguments"])
        for item in opposing:
            lines.append(f"- [{item.severity}] {item.argument_text}")
        lines.extend(["", "## Decision Change Triggers"])
        for item in triggers:
            lines.append(f"- [{item.trigger_type}] {item.trigger_text}")
        lines.extend(["", "## QA"])
        if qa:
            lines.append(f"- Status: {qa.qa_status}")
            lines.append(f"- Forbidden language hits: {qa.forbidden_language_count}")
            for reason in qa.failure_reasons:
                lines.append(f"- Failure: {reason}")
            for warning in qa.warnings:
                lines.append(f"- Warning: {warning}")
        else:
            lines.append("- Status: not_run")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, senior_memo_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(senior_memo_id)), encoding="utf-8")
        return output_path
