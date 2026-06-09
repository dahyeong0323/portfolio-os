from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from typing import Any, Sequence

from portfolio_os.db.connection import Database
from portfolio_os.senior.models import (
    DecisionCandidate,
    DecisionChangeTrigger,
    NoActionAlternative,
    OpposingArgument,
    SeniorMemo,
    SeniorMemoInputBundle,
    SeniorMemoQAResult,
    SeniorMemoSection,
)
from portfolio_os.serialization import dumps_json, loads_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, require_text


def _bool(value: Any) -> bool:
    return bool(int(value))


def _dt(value: str | None) -> datetime | None:
    return datetime_from_text(value) if value else None


def _int_tuple(value: str) -> tuple[int, ...]:
    loaded = loads_json(value)
    if not isinstance(loaded, list):
        return ()
    return tuple(int(item) for item in loaded)


def _str_tuple(value: str) -> tuple[str, ...]:
    loaded = loads_json(value)
    if not isinstance(loaded, list):
        return ()
    return tuple(str(item) for item in loaded)


def bundle_from_row(row: dict[str, Any]) -> SeniorMemoInputBundle:
    return SeniorMemoInputBundle(
        row["input_bundle_id"],
        date_from_text(row["as_of_date"]),
        row["ledger_status"],
        row["latest_reconciliation_id"],
        _bool(row["portfolio_only"]),
        _int_tuple(row["research_packet_ids_json"]),
        row["macro_context_packet_id"],
        _int_tuple(row["risk_validation_ids_json"]),
        _int_tuple(row["order_ticket_ids_json"]),
        _int_tuple(row["manual_execution_ids_json"]),
        _int_tuple(row["override_ticket_ids_json"]),
        _int_tuple(row["decision_journal_ids_json"]),
        row["input_digest"],
        _dt(row["created_at"]),
    )


def memo_from_row(row: dict[str, Any]) -> SeniorMemo:
    return SeniorMemo(
        row["senior_memo_id"],
        row["input_bundle_id"],
        row["memo_title"],
        date_from_text(row["as_of_date"]),
        row["memo_status"],
        row["memo_scope"],
        row["memo_recommendation_scope"],
        row["executive_summary"],
        row["confidence_level"],
        row["primary_risk_summary"],
        _bool(row["no_action_is_acceptable"]),
        row["qa_status"],
        row["created_by"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def section_from_row(row: dict[str, Any]) -> SeniorMemoSection:
    return SeniorMemoSection(row["section_id"], row["senior_memo_id"], row["section_type"], row["section_title"], row["section_text"], _str_tuple(row["source_refs_json"]), _dt(row["created_at"]))


def candidate_from_row(row: dict[str, Any]) -> DecisionCandidate:
    return DecisionCandidate(
        row["decision_candidate_id"],
        row["senior_memo_id"],
        row["instrument_id"],
        row["candidate_type"],
        row["candidate_action_class"],
        row["candidate_text"],
        row["rationale"],
        row["required_next_step"],
        row["candidate_status"],
        row["priority"],
        _bool(row["risk_validation_required"]),
        _bool(row["reconciliation_required_first"]),
        _dt(row["created_at"]),
    )


def no_action_from_row(row: dict[str, Any]) -> NoActionAlternative:
    return NoActionAlternative(row["no_action_id"], row["senior_memo_id"], row["alternative_text"], row["why_reasonable"], row["opportunity_cost"], row["risk_reduction_benefit"], row["review_trigger"], _dt(row["created_at"]))


def opposing_from_row(row: dict[str, Any]) -> OpposingArgument:
    return OpposingArgument(row["opposing_argument_id"], row["senior_memo_id"], row["argument_text"], row["severity"], _str_tuple(row["source_refs_json"]), _dt(row["created_at"]))


def trigger_from_row(row: dict[str, Any]) -> DecisionChangeTrigger:
    return DecisionChangeTrigger(row["change_trigger_id"], row["senior_memo_id"], row["trigger_text"], row["trigger_type"], row["monitoring_note"], _dt(row["created_at"]))


def qa_from_row(row: dict[str, Any]) -> SeniorMemoQAResult:
    return SeniorMemoQAResult(
        row["senior_memo_qa_id"],
        row["senior_memo_id"],
        row["qa_status"],
        row["required_section_count"],
        _str_tuple(row["missing_required_sections_json"]),
        row["candidate_count"],
        row["no_action_count"],
        row["opposing_argument_count"],
        row["change_trigger_count"],
        row["invalid_input_count"],
        row["forbidden_language_count"],
        _str_tuple(row["failure_reasons_json"]),
        _str_tuple(row["warnings_json"]),
        _dt(row["created_at"]),
    )


class SeniorMemoInputBundleRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_bundle(
        self,
        as_of_date: date,
        ledger_status: str,
        latest_reconciliation_id: int | None,
        portfolio_only: bool,
        research_packet_ids: Sequence[int],
        macro_context_packet_id: int | None,
        risk_validation_ids: Sequence[int],
        order_ticket_ids: Sequence[int],
        manual_execution_ids: Sequence[int],
        override_ticket_ids: Sequence[int],
        decision_journal_ids: Sequence[int],
        input_digest: str | None,
    ) -> SeniorMemoInputBundle:
        cursor = self.db.execute(
            """
            INSERT INTO senior_memo_input_bundles(as_of_date, ledger_status, latest_reconciliation_id, portfolio_only,
            research_packet_ids_json, macro_context_packet_id, risk_validation_ids_json, order_ticket_ids_json,
            manual_execution_ids_json, override_ticket_ids_json, decision_journal_ids_json, input_digest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date_to_text(as_of_date),
                ledger_status,
                latest_reconciliation_id,
                int(portfolio_only),
                dumps_json(tuple(research_packet_ids)),
                macro_context_packet_id,
                dumps_json(tuple(risk_validation_ids)),
                dumps_json(tuple(order_ticket_ids)),
                dumps_json(tuple(manual_execution_ids)),
                dumps_json(tuple(override_ticket_ids)),
                dumps_json(tuple(decision_journal_ids)),
                input_digest,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, input_bundle_id: int) -> SeniorMemoInputBundle:
        row = self.db.fetch_one("SELECT * FROM senior_memo_input_bundles WHERE input_bundle_id = ?", (input_bundle_id,))
        if row is None:
            raise ValueError(f"senior input bundle not found: {input_bundle_id}")
        return bundle_from_row(row)


class SeniorMemoRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_memo(self, input_bundle_id: int, memo_title: str, as_of_date: date, memo_scope: str, memo_recommendation_scope: str, executive_summary: str, confidence_level: str = "medium", primary_risk_summary: str | None = None, no_action_is_acceptable: bool = True, created_by: str = "human") -> SeniorMemo:
        require_text(memo_title, "memo_title")
        require_text(executive_summary, "executive_summary")
        cursor = self.db.execute(
            """
            INSERT INTO senior_memos(input_bundle_id, memo_title, as_of_date, memo_scope, memo_recommendation_scope,
            executive_summary, confidence_level, primary_risk_summary, no_action_is_acceptable, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (input_bundle_id, memo_title, date_to_text(as_of_date), memo_scope, memo_recommendation_scope, executive_summary, confidence_level, primary_risk_summary, int(no_action_is_acceptable), created_by),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, senior_memo_id: int) -> SeniorMemo:
        row = self.db.fetch_one("SELECT * FROM senior_memos WHERE senior_memo_id = ?", (senior_memo_id,))
        if row is None:
            raise ValueError(f"senior memo not found: {senior_memo_id}")
        return memo_from_row(row)

    def update_status(self, senior_memo_id: int, memo_status: str, qa_status: str) -> SeniorMemo:
        self.db.execute(
            "UPDATE senior_memos SET memo_status = ?, qa_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE senior_memo_id = ?",
            (memo_status, qa_status, senior_memo_id),
        )
        self.db.commit()
        return self.get(senior_memo_id)

    def archive(self, senior_memo_id: int) -> SeniorMemo:
        return self.update_status(senior_memo_id, "archived", self.get(senior_memo_id).qa_status)


class SeniorMemoSectionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add_section(self, senior_memo_id: int, section_type: str, section_title: str, section_text: str, source_refs: Sequence[str] = ()) -> SeniorMemoSection:
        require_text(section_title, "section_title")
        require_text(section_text, "section_text")
        cursor = self.db.execute(
            "INSERT INTO senior_memo_sections(senior_memo_id, section_type, section_title, section_text, source_refs_json) VALUES (?, ?, ?, ?, ?)",
            (senior_memo_id, section_type, section_title, section_text, dumps_json(tuple(source_refs))),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, section_id: int) -> SeniorMemoSection:
        row = self.db.fetch_one("SELECT * FROM senior_memo_sections WHERE section_id = ?", (section_id,))
        if row is None:
            raise ValueError(f"senior memo section not found: {section_id}")
        return section_from_row(row)

    def list_sections(self, senior_memo_id: int) -> list[SeniorMemoSection]:
        return [section_from_row(row) for row in self.db.fetch_all("SELECT * FROM senior_memo_sections WHERE senior_memo_id = ? ORDER BY section_id", (senior_memo_id,))]


class DecisionCandidateRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add_candidate(self, senior_memo_id: int, instrument_id: int | None, candidate_type: str, candidate_action_class: str, candidate_text: str, rationale: str, required_next_step: str, candidate_status: str, priority: str, risk_validation_required: bool, reconciliation_required_first: bool) -> DecisionCandidate:
        require_text(candidate_text, "candidate_text")
        require_text(rationale, "rationale")
        cursor = self.db.execute(
            """
            INSERT INTO decision_candidates(senior_memo_id, instrument_id, candidate_type, candidate_action_class, candidate_text,
            rationale, required_next_step, candidate_status, priority, risk_validation_required, reconciliation_required_first)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (senior_memo_id, instrument_id, candidate_type, candidate_action_class, candidate_text, rationale, required_next_step, candidate_status, priority, int(risk_validation_required), int(reconciliation_required_first)),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, decision_candidate_id: int) -> DecisionCandidate:
        row = self.db.fetch_one("SELECT * FROM decision_candidates WHERE decision_candidate_id = ?", (decision_candidate_id,))
        if row is None:
            raise ValueError(f"decision candidate not found: {decision_candidate_id}")
        return candidate_from_row(row)

    def list_candidates(self, senior_memo_id: int) -> list[DecisionCandidate]:
        return [candidate_from_row(row) for row in self.db.fetch_all("SELECT * FROM decision_candidates WHERE senior_memo_id = ? ORDER BY decision_candidate_id", (senior_memo_id,))]


class NoActionAlternativeRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, senior_memo_id: int, alternative_text: str, why_reasonable: str, opportunity_cost: str | None = None, risk_reduction_benefit: str | None = None, review_trigger: str | None = None) -> NoActionAlternative:
        require_text(alternative_text, "alternative_text")
        require_text(why_reasonable, "why_reasonable")
        cursor = self.db.execute(
            "INSERT INTO no_action_alternatives(senior_memo_id, alternative_text, why_reasonable, opportunity_cost, risk_reduction_benefit, review_trigger) VALUES (?, ?, ?, ?, ?, ?)",
            (senior_memo_id, alternative_text, why_reasonable, opportunity_cost, risk_reduction_benefit, review_trigger),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, no_action_id: int) -> NoActionAlternative:
        row = self.db.fetch_one("SELECT * FROM no_action_alternatives WHERE no_action_id = ?", (no_action_id,))
        if row is None:
            raise ValueError(f"no-action alternative not found: {no_action_id}")
        return no_action_from_row(row)

    def list_for_memo(self, senior_memo_id: int) -> list[NoActionAlternative]:
        return [no_action_from_row(row) for row in self.db.fetch_all("SELECT * FROM no_action_alternatives WHERE senior_memo_id = ? ORDER BY no_action_id", (senior_memo_id,))]


class OpposingArgumentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, senior_memo_id: int, argument_text: str, severity: str = "medium", source_refs: Sequence[str] = ()) -> OpposingArgument:
        require_text(argument_text, "argument_text")
        cursor = self.db.execute(
            "INSERT INTO opposing_arguments(senior_memo_id, argument_text, severity, source_refs_json) VALUES (?, ?, ?, ?)",
            (senior_memo_id, argument_text, severity, dumps_json(tuple(source_refs))),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, opposing_argument_id: int) -> OpposingArgument:
        row = self.db.fetch_one("SELECT * FROM opposing_arguments WHERE opposing_argument_id = ?", (opposing_argument_id,))
        if row is None:
            raise ValueError(f"opposing argument not found: {opposing_argument_id}")
        return opposing_from_row(row)

    def list_for_memo(self, senior_memo_id: int) -> list[OpposingArgument]:
        return [opposing_from_row(row) for row in self.db.fetch_all("SELECT * FROM opposing_arguments WHERE senior_memo_id = ? ORDER BY opposing_argument_id", (senior_memo_id,))]


class DecisionChangeTriggerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, senior_memo_id: int, trigger_text: str, trigger_type: str, monitoring_note: str | None = None) -> DecisionChangeTrigger:
        require_text(trigger_text, "trigger_text")
        cursor = self.db.execute(
            "INSERT INTO decision_change_triggers(senior_memo_id, trigger_text, trigger_type, monitoring_note) VALUES (?, ?, ?, ?)",
            (senior_memo_id, trigger_text, trigger_type, monitoring_note),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, change_trigger_id: int) -> DecisionChangeTrigger:
        row = self.db.fetch_one("SELECT * FROM decision_change_triggers WHERE change_trigger_id = ?", (change_trigger_id,))
        if row is None:
            raise ValueError(f"decision change trigger not found: {change_trigger_id}")
        return trigger_from_row(row)

    def list_for_memo(self, senior_memo_id: int) -> list[DecisionChangeTrigger]:
        return [trigger_from_row(row) for row in self.db.fetch_all("SELECT * FROM decision_change_triggers WHERE senior_memo_id = ? ORDER BY change_trigger_id", (senior_memo_id,))]


class SeniorMemoQARepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_result(self, result: SeniorMemoQAResult) -> SeniorMemoQAResult:
        cursor = self.db.execute(
            """
            INSERT INTO senior_memo_qa_results(senior_memo_id, qa_status, required_section_count, missing_required_sections_json,
            candidate_count, no_action_count, opposing_argument_count, change_trigger_count, invalid_input_count,
            forbidden_language_count, failure_reasons_json, warnings_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.senior_memo_id,
                result.qa_status,
                result.required_section_count,
                dumps_json(result.missing_required_sections),
                result.candidate_count,
                result.no_action_count,
                result.opposing_argument_count,
                result.change_trigger_count,
                result.invalid_input_count,
                result.forbidden_language_count,
                dumps_json(result.failure_reasons),
                dumps_json(result.warnings),
            ),
        )
        self.db.commit()
        return replace(result, senior_memo_qa_id=cursor.lastrowid)

    def get_latest_result(self, senior_memo_id: int) -> SeniorMemoQAResult | None:
        row = self.db.fetch_one("SELECT * FROM senior_memo_qa_results WHERE senior_memo_id = ? ORDER BY senior_memo_qa_id DESC LIMIT 1", (senior_memo_id,))
        return qa_from_row(row) if row else None
