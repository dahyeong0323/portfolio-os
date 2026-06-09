from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Sequence

from portfolio_os.db.connection import Database
from portfolio_os.macro.models import (
    CorrelationSnapshot,
    CrashPlaybookRule,
    MacroContextPacket,
    MacroMetricSnapshot,
    MacroRegimeSnapshot,
    PortfolioContextSnapshot,
)
from portfolio_os.serialization import dumps_json, loads_json
from portfolio_os.validators import date_from_text, date_to_text, datetime_from_text, decimal_from_text, decimal_to_text, require_text


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


def context_from_row(row: dict[str, Any]) -> PortfolioContextSnapshot:
    return PortfolioContextSnapshot(
        row["portfolio_context_id"],
        date_from_text(row["as_of_date"]),
        row["ledger_status"],
        row["latest_reconciliation_id"],
        row["open_ticket_count"],
        row["pending_execution_count"],
        row["open_override_count"],
        row["active_instrument_count"],
        row["context_json"],
        _dt(row["created_at"]),
    )


def metric_from_row(row: dict[str, Any]) -> MacroMetricSnapshot:
    return MacroMetricSnapshot(
        row["macro_metric_id"],
        date_from_text(row["metric_date"]),
        row["metric_code"],
        decimal_from_text(row["metric_value"], "metric_value"),
        row["metric_unit"],
        row["source_id"],
        row["notes"],
        _dt(row["created_at"]),
    )


def correlation_from_row(row: dict[str, Any]) -> CorrelationSnapshot:
    return CorrelationSnapshot(
        row["correlation_id"],
        date_from_text(row["as_of_date"]),
        row["left_symbol"],
        row["right_symbol"],
        row["metric_type"],
        row["window_days"],
        decimal_from_text(row["value"], "value"),
        row["source"],
        row["source_id"],
        row["notes"],
        _dt(row["created_at"]),
    )


def regime_from_row(row: dict[str, Any]) -> MacroRegimeSnapshot:
    return MacroRegimeSnapshot(
        row["macro_regime_id"],
        date_from_text(row["as_of_date"]),
        row["regime"],
        row["confidence"],
        row["reason_summary"],
        _int_tuple(row["metric_refs_json"]),
        _dt(row["created_at"]),
    )


def crash_rule_from_row(row: dict[str, Any]) -> CrashPlaybookRule:
    return CrashPlaybookRule(
        row["crash_rule_id"],
        row["rule_name"],
        row["trigger_conditions_json"],
        row["context_note"],
        row["forbidden_uses_json"],
        _bool(row["is_active"]),
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


def macro_packet_from_row(row: dict[str, Any]) -> MacroContextPacket:
    return MacroContextPacket(
        row["macro_context_packet_id"],
        row["portfolio_context_id"],
        row["macro_regime_id"],
        date_from_text(row["as_of_date"]),
        row["risk_on_exposure"],
        row["liquidity_sensitivity"],
        row["btc_related_exposure"],
        row["nasdaq_growth_exposure"],
        row["correlation_stress"],
        row["defensive_buffer"],
        row["summary_text"],
        _int_tuple(row["metric_refs_json"]),
        _int_tuple(row["correlation_refs_json"]),
        _int_tuple(row["crash_rule_refs_json"]),
        _str_tuple(row["unknowns_json"]),
        row["packet_status"],
        _dt(row["created_at"]),
        _dt(row["updated_at"]),
    )


class PortfolioContextRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_context_snapshot(self, as_of_date: date, ledger_status: str, latest_reconciliation_id: int | None, open_ticket_count: int, pending_execution_count: int, open_override_count: int, active_instrument_count: int, context_json: str) -> PortfolioContextSnapshot:
        cursor = self.db.execute(
            """
            INSERT INTO portfolio_context_snapshots(as_of_date, ledger_status, latest_reconciliation_id, open_ticket_count,
            pending_execution_count, open_override_count, active_instrument_count, context_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date_to_text(as_of_date), ledger_status, latest_reconciliation_id, open_ticket_count, pending_execution_count, open_override_count, active_instrument_count, context_json),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, portfolio_context_id: int) -> PortfolioContextSnapshot:
        row = self.db.fetch_one("SELECT * FROM portfolio_context_snapshots WHERE portfolio_context_id = ?", (portfolio_context_id,))
        if row is None:
            raise ValueError(f"portfolio context not found: {portfolio_context_id}")
        return context_from_row(row)

    def get_latest_context(self, as_of_date: date | None = None) -> PortfolioContextSnapshot | None:
        if as_of_date is None:
            row = self.db.fetch_one("SELECT * FROM portfolio_context_snapshots ORDER BY as_of_date DESC, portfolio_context_id DESC LIMIT 1")
        else:
            row = self.db.fetch_one("SELECT * FROM portfolio_context_snapshots WHERE as_of_date <= ? ORDER BY as_of_date DESC, portfolio_context_id DESC LIMIT 1", (date_to_text(as_of_date),))
        return context_from_row(row) if row else None


class MacroMetricRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_metric(self, metric_date: date, metric_code: str, metric_value: Decimal, metric_unit: str, source_id: int | None = None, notes: str | None = None) -> MacroMetricSnapshot:
        require_text(metric_code, "metric_code")
        cursor = self.db.execute(
            "INSERT INTO macro_metric_snapshots(metric_date, metric_code, metric_value, metric_unit, source_id, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (date_to_text(metric_date), metric_code, decimal_to_text(metric_value, "metric_value"), metric_unit, source_id, notes),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, macro_metric_id: int) -> MacroMetricSnapshot:
        row = self.db.fetch_one("SELECT * FROM macro_metric_snapshots WHERE macro_metric_id = ?", (macro_metric_id,))
        if row is None:
            raise ValueError(f"macro metric not found: {macro_metric_id}")
        return metric_from_row(row)

    def list_metrics(self, metric_code: str | None = None, as_of_date: date | None = None) -> list[MacroMetricSnapshot]:
        sql = "SELECT * FROM macro_metric_snapshots WHERE 1 = 1"
        params: list[Any] = []
        if metric_code:
            sql += " AND metric_code = ?"
            params.append(metric_code)
        if as_of_date:
            sql += " AND metric_date <= ?"
            params.append(date_to_text(as_of_date))
        sql += " ORDER BY metric_date, macro_metric_id"
        return [metric_from_row(row) for row in self.db.fetch_all(sql, params)]


class CorrelationRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_correlation(self, as_of_date: date, left_symbol: str, right_symbol: str, metric_type: str, window_days: int, value: Decimal, source: str = "manual", source_id: int | None = None, notes: str | None = None) -> CorrelationSnapshot:
        require_text(left_symbol, "left_symbol")
        require_text(right_symbol, "right_symbol")
        if metric_type == "correlation" and not (Decimal("-1") <= value <= Decimal("1")):
            raise ValueError("correlation value must be between -1 and 1")
        if window_days <= 0:
            raise ValueError("window_days must be positive")
        cursor = self.db.execute(
            """
            INSERT INTO correlation_snapshots(as_of_date, left_symbol, right_symbol, metric_type, window_days, value, source, source_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (date_to_text(as_of_date), left_symbol, right_symbol, metric_type, window_days, decimal_to_text(value, "value"), source, source_id, notes),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, correlation_id: int) -> CorrelationSnapshot:
        row = self.db.fetch_one("SELECT * FROM correlation_snapshots WHERE correlation_id = ?", (correlation_id,))
        if row is None:
            raise ValueError(f"correlation not found: {correlation_id}")
        return correlation_from_row(row)

    def list_correlations(self, as_of_date: date | None = None) -> list[CorrelationSnapshot]:
        if as_of_date is None:
            rows = self.db.fetch_all("SELECT * FROM correlation_snapshots ORDER BY as_of_date, correlation_id")
        else:
            rows = self.db.fetch_all("SELECT * FROM correlation_snapshots WHERE as_of_date <= ? ORDER BY as_of_date, correlation_id", (date_to_text(as_of_date),))
        return [correlation_from_row(row) for row in rows]


class MacroRegimeRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_regime(self, as_of_date: date, regime: str, confidence: str, reason_summary: str, metric_refs: Sequence[int] = ()) -> MacroRegimeSnapshot:
        require_text(reason_summary, "reason_summary")
        cursor = self.db.execute(
            "INSERT INTO macro_regime_snapshots(as_of_date, regime, confidence, reason_summary, metric_refs_json) VALUES (?, ?, ?, ?, ?)",
            (date_to_text(as_of_date), regime, confidence, reason_summary, dumps_json(tuple(metric_refs))),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, macro_regime_id: int) -> MacroRegimeSnapshot:
        row = self.db.fetch_one("SELECT * FROM macro_regime_snapshots WHERE macro_regime_id = ?", (macro_regime_id,))
        if row is None:
            raise ValueError(f"macro regime not found: {macro_regime_id}")
        return regime_from_row(row)

    def get_latest_regime(self, as_of_date: date | None = None) -> MacroRegimeSnapshot | None:
        if as_of_date is None:
            row = self.db.fetch_one("SELECT * FROM macro_regime_snapshots ORDER BY as_of_date DESC, macro_regime_id DESC LIMIT 1")
        else:
            row = self.db.fetch_one("SELECT * FROM macro_regime_snapshots WHERE as_of_date <= ? ORDER BY as_of_date DESC, macro_regime_id DESC LIMIT 1", (date_to_text(as_of_date),))
        return regime_from_row(row) if row else None


class CrashPlaybookRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_rule(self, rule_name: str, trigger_conditions_json: str, context_note: str, forbidden_uses_json: str = "[]") -> CrashPlaybookRule:
        require_text(rule_name, "rule_name")
        require_text(context_note, "context_note")
        cursor = self.db.execute(
            "INSERT INTO crash_playbook_rules(rule_name, trigger_conditions_json, context_note, forbidden_uses_json, is_active) VALUES (?, ?, ?, ?, 1)",
            (rule_name, trigger_conditions_json, context_note, forbidden_uses_json),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, crash_rule_id: int) -> CrashPlaybookRule:
        row = self.db.fetch_one("SELECT * FROM crash_playbook_rules WHERE crash_rule_id = ?", (crash_rule_id,))
        if row is None:
            raise ValueError(f"crash rule not found: {crash_rule_id}")
        return crash_rule_from_row(row)

    def list_active(self) -> list[CrashPlaybookRule]:
        return [crash_rule_from_row(row) for row in self.db.fetch_all("SELECT * FROM crash_playbook_rules WHERE is_active = 1 ORDER BY crash_rule_id")]


class MacroContextPacketRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_packet(self, portfolio_context_id: int | None, macro_regime_id: int | None, as_of_date: date, risk_on_exposure: str, liquidity_sensitivity: str, btc_related_exposure: str, nasdaq_growth_exposure: str, correlation_stress: str, defensive_buffer: str, summary_text: str, metric_refs: Sequence[int] = (), correlation_refs: Sequence[int] = (), crash_rule_refs: Sequence[int] = (), unknowns: Sequence[str] = ()) -> MacroContextPacket:
        require_text(summary_text, "summary_text")
        cursor = self.db.execute(
            """
            INSERT INTO macro_context_packets(portfolio_context_id, macro_regime_id, as_of_date, risk_on_exposure, liquidity_sensitivity,
            btc_related_exposure, nasdaq_growth_exposure, correlation_stress, defensive_buffer, summary_text,
            metric_refs_json, correlation_refs_json, crash_rule_refs_json, unknowns_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                portfolio_context_id,
                macro_regime_id,
                date_to_text(as_of_date),
                risk_on_exposure,
                liquidity_sensitivity,
                btc_related_exposure,
                nasdaq_growth_exposure,
                correlation_stress,
                defensive_buffer,
                summary_text,
                dumps_json(tuple(metric_refs)),
                dumps_json(tuple(correlation_refs)),
                dumps_json(tuple(crash_rule_refs)),
                dumps_json(tuple(unknowns)),
            ),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, macro_context_packet_id: int) -> MacroContextPacket:
        row = self.db.fetch_one("SELECT * FROM macro_context_packets WHERE macro_context_packet_id = ?", (macro_context_packet_id,))
        if row is None:
            raise ValueError(f"macro context packet not found: {macro_context_packet_id}")
        return macro_packet_from_row(row)

    def update_status(self, macro_context_packet_id: int, status: str) -> MacroContextPacket:
        self.db.execute(
            "UPDATE macro_context_packets SET packet_status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now') WHERE macro_context_packet_id = ?",
            (status, macro_context_packet_id),
        )
        self.db.commit()
        return self.get(macro_context_packet_id)
