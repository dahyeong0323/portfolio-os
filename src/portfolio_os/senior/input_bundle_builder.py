from __future__ import annotations

import hashlib
from datetime import date

from portfolio_os.db.connection import Database
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.macro.repositories import MacroContextPacketRepository
from portfolio_os.research.repositories import ResearchPacketRepository
from portfolio_os.repositories import ReconciliationRepository
from portfolio_os.senior.repositories import SeniorMemoInputBundleRepository
from portfolio_os.serialization import dumps_json


class SeniorMemoInputBundleBuilder:
    def __init__(self, db: Database) -> None:
        self.db = db

    def build_bundle(
        self,
        as_of_date: date,
        research_packet_ids: tuple[int, ...] = (),
        macro_context_packet_id: int | None = None,
        portfolio_only: bool = False,
        include_recent_risk_context: bool = True,
    ):
        if not research_packet_ids and not portfolio_only:
            raise ValueError("research_packet_ids are required unless portfolio_only is true")

        research_repo = ResearchPacketRepository(self.db)
        research_refs: list[dict] = []
        for packet_id in research_packet_ids:
            packet = research_repo.get(packet_id)
            if packet.packet_status != "valid" or packet.qa_status != "passed":
                raise ValueError(f"research packet is not valid/passed: {packet_id}")
            research_refs.append({"research_packet_id": packet_id, "status": packet.packet_status, "qa_status": packet.qa_status})

        macro_ref: dict | None = None
        if macro_context_packet_id is not None:
            macro_packet = MacroContextPacketRepository(self.db).get(macro_context_packet_id)
            if macro_packet.packet_status != "valid":
                raise ValueError(f"macro context packet is not valid: {macro_context_packet_id}")
            macro_ref = {"macro_context_packet_id": macro_context_packet_id, "status": macro_packet.packet_status}

        ledger = LedgerSnapshotBuilder(self.db).build_snapshot(as_of_date)
        latest_reconciliation = ReconciliationRepository(self.db).get_latest_reconciliation()
        risk_validation_ids: tuple[int, ...] = ()
        order_ticket_ids: tuple[int, ...] = ()
        manual_execution_ids: tuple[int, ...] = ()
        override_ticket_ids: tuple[int, ...] = ()
        decision_journal_ids: tuple[int, ...] = ()
        if include_recent_risk_context:
            risk_validation_ids = tuple(row["risk_validation_id"] for row in self.db.fetch_all("SELECT risk_validation_id FROM risk_validation_results ORDER BY risk_validation_id DESC LIMIT 20"))
            order_ticket_ids = tuple(row["order_ticket_id"] for row in self.db.fetch_all("SELECT order_ticket_id FROM order_tickets ORDER BY order_ticket_id DESC LIMIT 20"))
            manual_execution_ids = tuple(row["manual_execution_id"] for row in self.db.fetch_all("SELECT manual_execution_id FROM manual_execution_logs ORDER BY manual_execution_id DESC LIMIT 20"))
            override_ticket_ids = tuple(row["override_ticket_id"] for row in self.db.fetch_all("SELECT override_ticket_id FROM override_tickets ORDER BY override_ticket_id DESC LIMIT 20"))
            decision_journal_ids = tuple(row["decision_id"] for row in self.db.fetch_all("SELECT decision_id FROM decision_journal ORDER BY decision_id DESC LIMIT 20"))

        digest_payload = {
            "as_of_date": as_of_date.isoformat(),
            "ledger_status": ledger.ledger_status,
            "latest_reconciliation_id": latest_reconciliation["reconciliation_id"] if latest_reconciliation else None,
            "portfolio_only": portfolio_only,
            "research": research_refs,
            "macro": macro_ref,
            "risk_validation_ids": risk_validation_ids,
            "order_ticket_ids": order_ticket_ids,
            "manual_execution_ids": manual_execution_ids,
            "override_ticket_ids": override_ticket_ids,
            "decision_journal_ids": decision_journal_ids,
        }
        digest = hashlib.sha256(dumps_json(digest_payload).encode("utf-8")).hexdigest()
        return SeniorMemoInputBundleRepository(self.db).create_bundle(
            as_of_date=as_of_date,
            ledger_status=ledger.ledger_status,
            latest_reconciliation_id=latest_reconciliation["reconciliation_id"] if latest_reconciliation else None,
            portfolio_only=portfolio_only,
            research_packet_ids=research_packet_ids,
            macro_context_packet_id=macro_context_packet_id,
            risk_validation_ids=risk_validation_ids,
            order_ticket_ids=order_ticket_ids,
            manual_execution_ids=manual_execution_ids,
            override_ticket_ids=override_ticket_ids,
            decision_journal_ids=decision_journal_ids,
            input_digest=digest,
        )
