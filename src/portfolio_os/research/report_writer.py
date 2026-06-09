from __future__ import annotations

from pathlib import Path

from portfolio_os.db.connection import Database
from portfolio_os.research.repositories import (
    ResearchFactRepository,
    ResearchMissingDataRepository,
    ResearchPacketRepository,
    ResearchQARepository,
    ResearchSourceRepository,
)
from portfolio_os.repositories import InstrumentRepository
from portfolio_os.serialization import dumps_json


class ResearchReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, research_packet_id: int) -> dict:
        packet = ResearchPacketRepository(self.db).get(research_packet_id)
        facts = ResearchFactRepository(self.db).list_facts(research_packet_id)
        missing = ResearchMissingDataRepository(self.db).list_missing_data(research_packet_id)
        qa = ResearchQARepository(self.db).get_latest_result(research_packet_id)
        instrument = InstrumentRepository(self.db).get_instrument(packet.instrument_id)
        source_repo = ResearchSourceRepository(self.db)
        sources = [source_repo.get(source_id) for source_id in sorted({fact.source_id for fact in facts})]
        return {"packet": packet, "instrument": instrument, "facts": facts, "missing_data": missing, "sources": sources, "qa": qa}

    def write_markdown_report(self, research_packet_id: int, output_path: Path) -> Path:
        payload = self._payload(research_packet_id)
        packet = payload["packet"]
        instrument = payload["instrument"]
        facts = payload["facts"]
        missing = payload["missing_data"]
        sources = payload["sources"]
        qa = payload["qa"]

        lines = [
            f"# Research Packet {packet.research_packet_id}",
            "",
            "This research report is a sourced fact packet only. It is not an order ticket, not a risk validation, and not an instruction.",
            "",
            "## Packet",
            f"- Instrument: {instrument.symbol if instrument else packet.instrument_id}",
            f"- As of date: {packet.as_of_date}",
            f"- Packet status: {packet.packet_status}",
            f"- QA status: {packet.qa_status}",
            f"- Summary: {packet.summary_text or ''}",
            "",
            "## Facts",
        ]
        for fact in facts:
            lines.append(f"- [{fact.fact_category}/{fact.thesis_relation}] {fact.fact_text}")
        lines.extend(["", "## Missing Data"])
        for item in missing:
            lines.append(f"- [{item.importance}] {item.data_question}")
        lines.extend(["", "## Sources"])
        for source in sources:
            ref = source.url or source.local_path or ""
            lines.append(f"- {source.title} ({source.source_type}) {ref}")
        lines.extend(["", "## QA"])
        if qa:
            lines.append(f"- Status: {qa.qa_status}")
            lines.append(f"- Forbidden language hits: {qa.forbidden_language_count}")
            for reason in qa.failure_reasons:
                lines.append(f"- Failure: {reason}")
        else:
            lines.append("- Status: not_run")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, research_packet_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(research_packet_id)), encoding="utf-8")
        return output_path
