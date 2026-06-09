from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from portfolio_os.macro.models import CorrelationSnapshot, MacroMetricSnapshot, MacroRegimeSnapshot


class MacroRegimeClassifier:
    def classify_regime(self, as_of_date: date, metrics: Sequence[MacroMetricSnapshot], correlations: Sequence[CorrelationSnapshot]) -> MacroRegimeSnapshot:
        if not metrics and not correlations:
            return MacroRegimeSnapshot(0, as_of_date, "unknown", "low", "No macro metrics or correlations were available.", (), None)

        regime = "normal"
        confidence = "medium"
        reasons: list[str] = []
        metric_refs: list[int] = []

        for metric in metrics:
            code = metric.metric_code.upper()
            value = metric.metric_value
            stress_threshold = Decimal("-0.15") if metric.metric_unit == "ratio" else Decimal("-15")
            crisis_threshold = Decimal("-0.30") if metric.metric_unit == "ratio" else Decimal("-30")
            if "DRAWDOWN" in code and value <= crisis_threshold:
                regime = "crisis"
                confidence = "high"
                reasons.append(f"{metric.metric_code} reached crisis drawdown level")
                metric_refs.append(metric.macro_metric_id)
            elif "DRAWDOWN" in code and value <= stress_threshold and regime != "crisis":
                regime = "stress"
                confidence = "medium"
                reasons.append(f"{metric.metric_code} reached stress drawdown level")
                metric_refs.append(metric.macro_metric_id)
            elif "VOLATILITY" in code and value >= Decimal("2"):
                regime = "crisis"
                confidence = "high"
                reasons.append(f"{metric.metric_code} reached crisis volatility level")
                metric_refs.append(metric.macro_metric_id)
            elif "VOLATILITY" in code and value >= Decimal("1.5") and regime != "crisis":
                regime = "stress"
                confidence = "medium"
                reasons.append(f"{metric.metric_code} reached stress volatility level")
                metric_refs.append(metric.macro_metric_id)

        for correlation in correlations:
            if correlation.metric_type == "correlation" and abs(correlation.value) >= Decimal("0.95"):
                regime = "crisis"
                confidence = "high"
                reasons.append(f"{correlation.left_symbol}/{correlation.right_symbol} correlation is extreme")
            elif correlation.metric_type == "correlation" and abs(correlation.value) >= Decimal("0.85") and regime != "crisis":
                regime = "stress"
                reasons.append(f"{correlation.left_symbol}/{correlation.right_symbol} correlation is elevated")

        if not reasons:
            reasons.append("Available macro metrics did not cross Stage 3 context thresholds.")
        return MacroRegimeSnapshot(0, as_of_date, regime, confidence, "; ".join(reasons), tuple(sorted(set(metric_refs))), None)
