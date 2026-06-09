from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from portfolio_os.macro.regime_classifier import MacroRegimeClassifier
from portfolio_os.macro.repositories import CorrelationRepository, MacroContextPacketRepository, MacroMetricRepository
from portfolio_os.macro.services import MacroContextService
from portfolio_os.validators import DecimalValidationError


def test_macro_metric_rejects_float_and_correlation_validates_range(db) -> None:
    with pytest.raises(DecimalValidationError):
        MacroMetricRepository(db).record_metric(date(2026, 2, 1), "NASDAQ_DRAWDOWN", 1.2, "ratio")
    with pytest.raises(ValueError):
        CorrelationRepository(db).record_correlation(date(2026, 2, 1), "PORTFOLIO", "QQQ", "correlation", 30, Decimal("1.20"))


def test_macro_regime_classifier_handles_unknown_and_stress(db) -> None:
    unknown = MacroRegimeClassifier().classify_regime(date(2026, 2, 1), (), ())
    assert unknown.regime == "unknown"
    from portfolio_os.macro.models import MacroMetricSnapshot

    stress_metric = MacroMetricSnapshot(1, date(2026, 2, 1), "NASDAQ_DRAWDOWN", Decimal("-0.20"), "ratio", None, None, None)
    stress = MacroRegimeClassifier().classify_regime(date(2026, 2, 1), (stress_metric,), ())
    assert stress.regime == "stress"


def test_macro_context_validation_fails_on_order_authority_language(db) -> None:
    packet = MacroContextService(db).create_macro_context_packet(date(2026, 2, 1), None, None, "This context says execute the order.")
    validated = MacroContextService(db).validate_macro_context_packet(packet.macro_context_packet_id)
    assert validated.packet_status == "invalid"
    stored = MacroContextPacketRepository(db).get(packet.macro_context_packet_id)
    assert stored.packet_status == "invalid"


def test_macro_context_validation_passes_unknown_marked_context(db) -> None:
    packet = MacroContextService(db).create_macro_context_packet(date(2026, 2, 1), None, None, "Macro indicators were reviewed as context only.", unknowns=("liquidity",))
    validated = MacroContextService(db).validate_macro_context_packet(packet.macro_context_packet_id)
    assert validated.packet_status == "valid"
