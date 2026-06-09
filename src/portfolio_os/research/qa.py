from __future__ import annotations

from portfolio_os.db.connection import Database
from portfolio_os.research.lint import ResearchLintService
from portfolio_os.research.models import ResearchQAResult
from portfolio_os.research.repositories import ResearchFactRepository, ResearchMissingDataRepository, ResearchPacketRepository, ResearchQARepository


class ResearchQAService:
    def __init__(self, db: Database, lint_service: ResearchLintService | None = None) -> None:
        self.db = db
        self.lint_service = lint_service or ResearchLintService()

    def run_qa(self, research_packet_id: int) -> ResearchQAResult:
        packet = ResearchPacketRepository(self.db).get(research_packet_id)
        facts = ResearchFactRepository(self.db).list_facts(research_packet_id)
        missing = ResearchMissingDataRepository(self.db).list_missing_data(research_packet_id)

        bull = sum(1 for fact in facts if fact.fact_category == "bull")
        bear = sum(1 for fact in facts if fact.fact_category == "bear")
        neutral = sum(1 for fact in facts if fact.fact_category == "neutral")
        supporting = sum(1 for fact in facts if fact.thesis_relation == "supporting")
        challenging = sum(1 for fact in facts if fact.thesis_relation == "challenging")
        source_count = len({fact.source_id for fact in facts})

        forbidden_hits: list[str] = []
        forbidden_hits.extend(self.lint_service.find_forbidden_language(packet.summary_text))
        for fact in facts:
            forbidden_hits.extend(self.lint_service.find_forbidden_language(fact.fact_text))

        failures: list[str] = []
        if bull < 1:
            failures.append("research packet requires at least one bull fact")
        if bear < 1:
            failures.append("research packet requires at least one bear fact")
        if neutral < 1:
            failures.append("research packet requires at least one neutral fact")
        if supporting < 1:
            failures.append("research packet requires at least one thesis-supporting fact")
        if challenging < 1:
            failures.append("research packet requires at least one thesis-challenging fact")
        if len(missing) < 1:
            failures.append("research packet requires at least one missing data item")
        if source_count < 1:
            failures.append("research packet requires at least one cited source")
        if forbidden_hits:
            failures.append("research packet contains forbidden recommendation or order-authority language")

        status = "failed" if failures else "passed"
        return ResearchQAResult(
            research_qa_id=0,
            research_packet_id=research_packet_id,
            qa_status=status,
            bull_fact_count=bull,
            bear_fact_count=bear,
            neutral_fact_count=neutral,
            supporting_fact_count=supporting,
            challenging_fact_count=challenging,
            missing_data_count=len(missing),
            source_count=source_count,
            forbidden_language_count=len(forbidden_hits),
            failure_reasons=tuple(failures),
            warnings=(),
            created_at=None,
        )

    def apply_qa_result(self, result: ResearchQAResult):
        saved = ResearchQARepository(self.db).save_result(result)
        packet_status = "valid" if saved.qa_status == "passed" else "invalid"
        qa_status = "passed" if saved.qa_status == "passed" else "failed"
        return ResearchPacketRepository(self.db).update_status(saved.research_packet_id, packet_status, qa_status)

    def run_and_apply(self, research_packet_id: int) -> ResearchQAResult:
        result = self.run_qa(research_packet_id)
        saved = ResearchQARepository(self.db).save_result(result)
        packet_status = "valid" if saved.qa_status == "passed" else "invalid"
        qa_status = "passed" if saved.qa_status == "passed" else "failed"
        ResearchPacketRepository(self.db).update_status(saved.research_packet_id, packet_status, qa_status)
        return saved
