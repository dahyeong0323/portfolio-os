from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from portfolio_os.db.connection import Database
from portfolio_os.macro.regime_classifier import MacroRegimeClassifier
from portfolio_os.macro.repositories import (
    CorrelationRepository,
    CrashPlaybookRepository,
    MacroContextPacketRepository,
    MacroMetricRepository,
    MacroRegimeRepository,
    PortfolioContextRepository,
)
from portfolio_os.research.lint import ResearchLintService


class MacroMetricService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record_metric(self, metric_date: date, metric_code: str, metric_value: Decimal, metric_unit: str, source_id: int | None = None, notes: str | None = None):
        return MacroMetricRepository(self.db).record_metric(metric_date, metric_code, metric_value, metric_unit, source_id, notes)

    def record_correlation(self, as_of_date: date, left_symbol: str, right_symbol: str, metric_type: str, window_days: int, value: Decimal, source: str = "manual", source_id: int | None = None, notes: str | None = None):
        return CorrelationRepository(self.db).record_correlation(as_of_date, left_symbol, right_symbol, metric_type, window_days, value, source, source_id, notes)

    def classify_and_record_regime(self, as_of_date: date):
        metrics = MacroMetricRepository(self.db).list_metrics(as_of_date=as_of_date)
        correlations = CorrelationRepository(self.db).list_correlations(as_of_date=as_of_date)
        classified = MacroRegimeClassifier().classify_regime(as_of_date, metrics, correlations)
        return MacroRegimeRepository(self.db).record_regime(classified.as_of_date, classified.regime, classified.confidence, classified.reason_summary, classified.metric_refs)


class MacroContextService:
    def __init__(self, db: Database, lint_service: ResearchLintService | None = None) -> None:
        self.db = db
        self.lint_service = lint_service or ResearchLintService()

    def create_macro_context_packet(
        self,
        as_of_date: date,
        portfolio_context_id: int | None,
        macro_regime_id: int | None,
        summary_text: str,
        risk_on_exposure: str = "unknown",
        liquidity_sensitivity: str = "unknown",
        btc_related_exposure: str = "unknown",
        nasdaq_growth_exposure: str = "unknown",
        correlation_stress: str = "unknown",
        defensive_buffer: str = "unknown",
        metric_refs: Sequence[int] = (),
        correlation_refs: Sequence[int] = (),
        crash_rule_refs: Sequence[int] = (),
        unknowns: Sequence[str] = (),
    ):
        if portfolio_context_id is not None:
            PortfolioContextRepository(self.db).get(portfolio_context_id)
        if macro_regime_id is not None:
            MacroRegimeRepository(self.db).get(macro_regime_id)
        return MacroContextPacketRepository(self.db).create_packet(
            portfolio_context_id,
            macro_regime_id,
            as_of_date,
            risk_on_exposure,
            liquidity_sensitivity,
            btc_related_exposure,
            nasdaq_growth_exposure,
            correlation_stress,
            defensive_buffer,
            summary_text,
            metric_refs,
            correlation_refs,
            crash_rule_refs,
            unknowns,
        )

    def validate_macro_context_packet(self, macro_context_packet_id: int):
        repo = MacroContextPacketRepository(self.db)
        packet = repo.get(macro_context_packet_id)
        failures: list[str] = []
        if self.lint_service.find_forbidden_language(packet.summary_text):
            failures.append("summary_text contains forbidden recommendation or order-authority language")
        if not packet.summary_text.strip():
            failures.append("summary_text is required")
        return repo.update_status(macro_context_packet_id, "invalid" if failures else "valid")

    def create_crash_playbook_rule(self, rule_name: str, trigger_conditions_json: str, context_note: str, forbidden_uses_json: str = "[]"):
        return CrashPlaybookRepository(self.db).create_rule(rule_name, trigger_conditions_json, context_note, forbidden_uses_json)
