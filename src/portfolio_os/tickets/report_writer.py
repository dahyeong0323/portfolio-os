from __future__ import annotations

from pathlib import Path

from portfolio_os.risk.models import OrderTicket
from portfolio_os.serialization import dumps_json


class OrderTicketReportWriter:
    def write_markdown_report(self, ticket: OrderTicket, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Order Ticket",
            "",
            f"- Order ticket ID: {ticket.order_ticket_id}",
            f"- Account ID: {ticket.account_id}",
            f"- Instrument ID: {ticket.instrument_id}",
            f"- Side: {ticket.side}",
            f"- Order type: {ticket.order_type}",
            f"- Quantity: {ticket.ticket_quantity}",
            f"- Limit price: {ticket.limit_price}",
            f"- Notional: {ticket.ticket_notional}",
            f"- Currency: {ticket.currency}",
            f"- Risk validation ID: {ticket.risk_validation_id}",
            f"- Status: {ticket.status}",
            f"- Expiry: {ticket.expires_at}",
            "",
            "The system does not execute this order.",
            "Place it manually in your external account interface only if you choose to approve it.",
            "After execution, log the actual filled quantity, price, fees, tax, and timestamp.",
        ]
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path

    def write_json_report(self, ticket: OrderTicket, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dumps_json(ticket), encoding="utf-8")
        return output_path
