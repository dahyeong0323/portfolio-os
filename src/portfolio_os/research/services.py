from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Sequence

from portfolio_os.db.connection import Database
from portfolio_os.research.lint import ResearchLintService
from portfolio_os.research.models import ResearchFact, ResearchMissingData, ResearchPacket
from portfolio_os.research.repositories import ResearchFactRepository, ResearchMissingDataRepository, ResearchPacketRepository, ResearchSourceRepository
from portfolio_os.repositories import InstrumentRepository


class ResearchPacketService:
    def __init__(self, db: Database, lint_service: ResearchLintService | None = None) -> None:
        self.db = db
        self.lint_service = lint_service or ResearchLintService()

    def create_research_packet(self, instrument_id: int, thesis_id: int | None, as_of_date: date, summary_text: str | None, packet_version: str = "v1", missing_data_summary: str | None = None, created_by: str = "human") -> ResearchPacket:
        if InstrumentRepository(self.db).get_instrument(instrument_id) is None:
            raise ValueError(f"instrument not found: {instrument_id}")
        return ResearchPacketRepository(self.db).create_packet(instrument_id, thesis_id, packet_version, as_of_date, summary_text, missing_data_summary, created_by)

    def add_fact_with_source(self, research_packet_id: int, source_id: int, fact_category: str, thesis_relation: str, fact_type: str, fact_text: str, numeric_value: Decimal | None = None, numeric_unit: str | None = None, observed_at: datetime | None = None) -> ResearchFact:
        ResearchPacketRepository(self.db).get(research_packet_id)
        ResearchSourceRepository(self.db).get(source_id)
        return ResearchFactRepository(self.db).add_fact(research_packet_id, source_id, fact_category, thesis_relation, fact_type, fact_text, numeric_value, numeric_unit, observed_at)

    def add_missing_data(self, research_packet_id: int, data_question: str, importance: str, attempted_sources: Sequence[str], impact_note: str | None) -> ResearchMissingData:
        ResearchPacketRepository(self.db).get(research_packet_id)
        return ResearchMissingDataRepository(self.db).add_missing_data(research_packet_id, data_question, importance, attempted_sources, impact_note)
