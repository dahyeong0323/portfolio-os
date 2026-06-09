from __future__ import annotations

from pathlib import Path

from portfolio_os.db.connection import Database
from portfolio_os.macro.repositories import MacroContextPacketRepository, MacroRegimeRepository, PortfolioContextRepository
from portfolio_os.serialization import dumps_json


class MacroContextReportWriter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def _payload(self, macro_context_packet_id: int) -> dict:
        packet = MacroContextPacketRepository(self.db).get(macro_context_packet_id)
        context = PortfolioContextRepository(self.db).get(packet.portfolio_context_id) if packet.portfolio_context_id else None
        regime = MacroRegimeRepository(self.db).get(packet.macro_regime_id) if packet.macro_regime_id else None
        return {"packet": packet, "portfolio_context": context, "macro_regime": regime}

    def write_markdown_report(self, macro_context_packet_id: int, output_path: Path) -> Path:
        payload = self._payload(macro_context_packet_id)
        packet = payload["packet"]
        context = payload["portfolio_context"]
        regime = payload["macro_regime"]
        lines = [
            f"# Macro Context Packet {packet.macro_context_packet_id}",
            "",
            "This macro context report is not an order ticket, not a risk validation, and not a recommendation.",
            "",
            f"- As of date: {packet.as_of_date}",
            f"- Packet status: {packet.packet_status}",
            f"- Ledger status: {context.ledger_status if context else 'unknown'}",
            f"- Macro regime: {regime.regime if regime else 'unknown'}",
            f"- Risk-on exposure: {packet.risk_on_exposure}",
            f"- Liquidity sensitivity: {packet.liquidity_sensitivity}",
            f"- BTC-related exposure: {packet.btc_related_exposure}",
            f"- Nasdaq/growth exposure: {packet.nasdaq_growth_exposure}",
            f"- Correlation stress: {packet.correlation_stress}",
            f"- Defensive buffer: {packet.defensive_buffer}",
            f"- Summary: {packet.summary_text}",
            f"- Metric refs: {', '.join(str(item) for item in packet.metric_refs) or 'none'}",
            f"- Correlation refs: {', '.join(str(item) for item in packet.correlation_refs) or 'none'}",
            f"- Crash playbook refs: {', '.join(str(item) for item in packet.crash_rule_refs) or 'none'}",
            f"- Unknown areas: {', '.join(packet.unknowns) or 'none'}",
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, macro_context_packet_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(self._payload(macro_context_packet_id)), encoding="utf-8")
        return output_path
