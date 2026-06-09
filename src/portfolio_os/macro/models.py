from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

MacroRegime = Literal["normal", "stress", "crisis", "unknown"]
ContextLevel = Literal["low", "medium", "high", "extreme", "unknown"]
MacroContextStatus = Literal["draft", "valid", "invalid", "archived"]


@dataclass(frozen=True)
class PortfolioContextSnapshot:
    portfolio_context_id: int
    as_of_date: date
    ledger_status: str
    latest_reconciliation_id: int | None
    open_ticket_count: int
    pending_execution_count: int
    open_override_count: int
    active_instrument_count: int
    context_json: str
    created_at: datetime | None


@dataclass(frozen=True)
class MacroMetricSnapshot:
    macro_metric_id: int
    metric_date: date
    metric_code: str
    metric_value: Decimal
    metric_unit: str
    source_id: int | None
    notes: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class CorrelationSnapshot:
    correlation_id: int
    as_of_date: date
    left_symbol: str
    right_symbol: str
    metric_type: Literal["correlation", "beta"]
    window_days: int
    value: Decimal
    source: str
    source_id: int | None
    notes: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class MacroRegimeSnapshot:
    macro_regime_id: int
    as_of_date: date
    regime: MacroRegime
    confidence: str
    reason_summary: str
    metric_refs: tuple[int, ...]
    created_at: datetime | None


@dataclass(frozen=True)
class CrashPlaybookRule:
    crash_rule_id: int
    rule_name: str
    trigger_conditions_json: str
    context_note: str
    forbidden_uses_json: str
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class MacroContextPacket:
    macro_context_packet_id: int
    portfolio_context_id: int | None
    macro_regime_id: int | None
    as_of_date: date
    risk_on_exposure: ContextLevel
    liquidity_sensitivity: str
    btc_related_exposure: str
    nasdaq_growth_exposure: str
    correlation_stress: str
    defensive_buffer: str
    summary_text: str
    metric_refs: tuple[int, ...]
    correlation_refs: tuple[int, ...]
    crash_rule_refs: tuple[int, ...]
    unknowns: tuple[str, ...]
    packet_status: MacroContextStatus
    created_at: datetime | None
    updated_at: datetime | None
