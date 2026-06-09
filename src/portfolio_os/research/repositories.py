from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Sequence

from portfolio_os.db.connection import Database
from portfolio_os.research.models import AssetThesis, ResearchFact, ResearchMissingData, ResearchPacket, ResearchQAResult, ResearchSource
from portfolio_os.serialization import dumps_json, loads_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, decimal_from_text, decimal_to_text, require_text


def _dt(value: str | None) -> datetime | None:
    return datetime_from_text(value) if value else None


def _tuple_json(value: str) -> tuple[Any, ...]:
    loaded = loads_json(value)
    return tuple(loaded if isinstance(loaded, list) else [])


def thesis_from_row(row: dict[str, Any]) -> AssetThesis:
    return AssetThesis(
        row["thesis_id"],
        row["instrument_id"],
        row["thesis_title"],
        row["thesis_text"],
        tuple(str(item) for item in _tuple_json(row["invalidation_triggers_json"])),
        tuple(str(item) for item in _tuple_json(row["watch_questions_json"])),
        row["status"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def source_from_row(row: dict[str, Any]) -> ResearchSource:
    return ResearchSource(
        row["source_id"],
        row["source_type"],
        row["title"],
        row["publisher"],
        row["url"],
        row["local_path"],
        _dt(row["published_at"]),
        _dt(row["retrieved_at"]),
        row["source_hash"],
        row["freshness_status"],
        row["reliability_note"],
    )


def packet_from_row(row: dict[str, Any]) -> ResearchPacket:
    return ResearchPacket(
        row["research_packet_id"],
        row["instrument_id"],
        row["thesis_id"],
        row["packet_version"],
        date_from_text(row["as_of_date"]),
        row["packet_status"],
        row["summary_text"],
        row["missing_data_summary"],
        row["qa_status"],
        row["created_by"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def fact_from_row(row: dict[str, Any]) -> ResearchFact:
    return ResearchFact(
        row["fact_id"],
        row["research_packet_id"],
        row["source_id"],
        row["fact_category"],
        row["thesis_relation"],
        row["fact_type"],
        row["fact_text"],
        decimal_from_text(row["numeric_value"], "numeric_value", allow_none=True),
        row["numeric_unit"],
        _dt(row["observed_at"]),
        _dt(row["created_at"]),
    )


def missing_from_row(row: dict[str, Any]) -> ResearchMissingData:
    return ResearchMissingData(
        row["missing_data_id"],
        row["research_packet_id"],
        row["data_question"],
        row["importance"],
        tuple(str(item) for item in _tuple_json(row["attempted_sources_json"])),
        row["impact_note"],
        _dt(row["created_at"]),
    )


def qa_from_row(row: dict[str, Any]) -> ResearchQAResult:
    return ResearchQAResult(
        row["research_qa_id"],
        row["research_packet_id"],
        row["qa_status"],
        row["bull_fact_count"],
        row["bear_fact_count"],
        row["neutral_fact_count"],
        row["supporting_fact_count"],
        row["challenging_fact_count"],
        row["missing_data_count"],
        row["source_count"],
        row["forbidden_language_count"],
        tuple(str(item) for item in _tuple_json(row["failure_reasons_json"])),
        tuple(str(item) for item in _tuple_json(row["warnings_json"])),
        _dt(row["created_at"]),
    )


class AssetThesisRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_thesis(self, instrument_id: int, thesis_title: str, thesis_text: str, invalidation_triggers: Sequence[str] = (), watch_questions: Sequence[str] = ()) -> AssetThesis:
        require_text(thesis_title, "thesis_title")
        require_text(thesis_text, "thesis_text")
        cursor = self.db.execute(
            """
            INSERT INTO asset_theses(instrument_id, thesis_title, thesis_text, invalidation_triggers_json, watch_questions_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (instrument_id, thesis_title, thesis_text, dumps_json(tuple(invalidation_triggers)), dumps_json(tuple(watch_questions))),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, thesis_id: int) -> AssetThesis:
        row = self.db.fetch_one("SELECT * FROM asset_theses WHERE thesis_id = ?", (thesis_id,))
        if row is None:
            raise ValueError(f"thesis not found: {thesis_id}")
        return thesis_from_row(row)

    def get_active_thesis(self, instrument_id: int) -> AssetThesis | None:
        row = self.db.fetch_one("SELECT * FROM asset_theses WHERE instrument_id = ? AND status = 'active' ORDER BY thesis_id DESC LIMIT 1", (instrument_id,))
        return thesis_from_row(row) if row else None

    def update_status(self, thesis_id: int, status: str) -> AssetThesis:
        self.db.execute(
            "UPDATE asset_theses SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE thesis_id = ?",
            (status, thesis_id),
        )
        self.db.commit()
        return self.get(thesis_id)


class ResearchSourceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_source(self, source_type: str, title: str, publisher: str | None = None, url: str | None = None, local_path: str | None = None, published_at: datetime | None = None, source_hash: str | None = None, freshness_status: str = "unknown", reliability_note: str | None = None) -> ResearchSource:
        require_text(title, "title")
        if not url and not local_path:
            raise ValueError("url or local_path is required")
        cursor = self.db.execute(
            """
            INSERT INTO research_sources(source_type, title, publisher, url, local_path, published_at, source_hash, freshness_status, reliability_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (source_type, title, publisher, url, local_path, published_at.isoformat().replace("+00:00", "Z") if published_at else None, source_hash, freshness_status, reliability_note),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, source_id: int) -> ResearchSource:
        row = self.db.fetch_one("SELECT * FROM research_sources WHERE source_id = ?", (source_id,))
        if row is None:
            raise ValueError(f"source not found: {source_id}")
        return source_from_row(row)

    def find_by_hash(self, source_hash: str) -> ResearchSource | None:
        row = self.db.fetch_one("SELECT * FROM research_sources WHERE source_hash = ? LIMIT 1", (source_hash,))
        return source_from_row(row) if row else None

    def list_sources(self) -> list[ResearchSource]:
        return [source_from_row(row) for row in self.db.fetch_all("SELECT * FROM research_sources ORDER BY source_id")]


class ResearchPacketRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_packet(self, instrument_id: int, thesis_id: int | None, packet_version: str, as_of_date: date, summary_text: str | None, missing_data_summary: str | None = None, created_by: str = "human") -> ResearchPacket:
        require_text(packet_version, "packet_version")
        cursor = self.db.execute(
            """
            INSERT INTO research_packets(instrument_id, thesis_id, packet_version, as_of_date, summary_text, missing_data_summary, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (instrument_id, thesis_id, packet_version, date_to_text(as_of_date), summary_text, missing_data_summary, created_by),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, research_packet_id: int) -> ResearchPacket:
        row = self.db.fetch_one("SELECT * FROM research_packets WHERE research_packet_id = ?", (research_packet_id,))
        if row is None:
            raise ValueError(f"research packet not found: {research_packet_id}")
        return packet_from_row(row)

    def update_status(self, research_packet_id: int, packet_status: str, qa_status: str) -> ResearchPacket:
        self.db.execute(
            """
            UPDATE research_packets
            SET packet_status = ?, qa_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
            WHERE research_packet_id = ?
            """,
            (packet_status, qa_status, research_packet_id),
        )
        self.db.commit()
        return self.get(research_packet_id)


class ResearchFactRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add_fact(self, research_packet_id: int, source_id: int, fact_category: str, thesis_relation: str, fact_type: str, fact_text: str, numeric_value: Decimal | None = None, numeric_unit: str | None = None, observed_at: datetime | None = None) -> ResearchFact:
        require_text(fact_text, "fact_text")
        cursor = self.db.execute(
            """
            INSERT INTO research_facts(research_packet_id, source_id, fact_category, thesis_relation, fact_type, fact_text, numeric_value, numeric_unit, observed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                research_packet_id,
                source_id,
                fact_category,
                thesis_relation,
                fact_type,
                fact_text,
                decimal_to_text(numeric_value, "numeric_value", allow_none=True),
                numeric_unit,
                observed_at.isoformat().replace("+00:00", "Z") if observed_at else None,
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, fact_id: int) -> ResearchFact:
        row = self.db.fetch_one("SELECT * FROM research_facts WHERE fact_id = ?", (fact_id,))
        if row is None:
            raise ValueError(f"research fact not found: {fact_id}")
        return fact_from_row(row)

    def list_facts(self, research_packet_id: int) -> list[ResearchFact]:
        return [fact_from_row(row) for row in self.db.fetch_all("SELECT * FROM research_facts WHERE research_packet_id = ? ORDER BY fact_id", (research_packet_id,))]


class ResearchMissingDataRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add_missing_data(self, research_packet_id: int, data_question: str, importance: str = "medium", attempted_sources: Sequence[str] = (), impact_note: str | None = None) -> ResearchMissingData:
        require_text(data_question, "data_question")
        cursor = self.db.execute(
            """
            INSERT INTO research_missing_data(research_packet_id, data_question, importance, attempted_sources_json, impact_note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (research_packet_id, data_question, importance, dumps_json(tuple(attempted_sources)), impact_note),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, missing_data_id: int) -> ResearchMissingData:
        row = self.db.fetch_one("SELECT * FROM research_missing_data WHERE missing_data_id = ?", (missing_data_id,))
        if row is None:
            raise ValueError(f"missing data not found: {missing_data_id}")
        return missing_from_row(row)

    def list_missing_data(self, research_packet_id: int) -> list[ResearchMissingData]:
        return [missing_from_row(row) for row in self.db.fetch_all("SELECT * FROM research_missing_data WHERE research_packet_id = ? ORDER BY missing_data_id", (research_packet_id,))]


class ResearchQARepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_result(self, result: ResearchQAResult) -> ResearchQAResult:
        cursor = self.db.execute(
            """
            INSERT INTO research_qa_results(research_packet_id, qa_status, bull_fact_count, bear_fact_count, neutral_fact_count,
            supporting_fact_count, challenging_fact_count, missing_data_count, source_count, forbidden_language_count,
            failure_reasons_json, warnings_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.research_packet_id,
                result.qa_status,
                result.bull_fact_count,
                result.bear_fact_count,
                result.neutral_fact_count,
                result.supporting_fact_count,
                result.challenging_fact_count,
                result.missing_data_count,
                result.source_count,
                result.forbidden_language_count,
                dumps_json(result.failure_reasons),
                dumps_json(result.warnings),
            ),
        )
        self.db.commit()
        return replace(result, research_qa_id=cursor.lastrowid)

    def get_latest_result(self, research_packet_id: int) -> ResearchQAResult | None:
        row = self.db.fetch_one(
            "SELECT * FROM research_qa_results WHERE research_packet_id = ? ORDER BY research_qa_id DESC LIMIT 1",
            (research_packet_id,),
        )
        return qa_from_row(row) if row else None
