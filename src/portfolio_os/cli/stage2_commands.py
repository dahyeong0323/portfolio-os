from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_os.db import Database
from portfolio_os.execution import ManualExecutionRepository, ManualExecutionService
from portfolio_os.intents import TransactionIntentRepository, TransactionIntentService
from portfolio_os.journal import DecisionJournalRepository, PostmortemTaskRepository
from portfolio_os.ledger import LedgerSnapshotBuilder
from portfolio_os.override import OverrideService, OverrideTicketRepository
from portfolio_os.pricing import PricingRepository
from portfolio_os.risk import RiskEngine, seed_default_risk_policy
from portfolio_os.risk.models import RiskRule
from portfolio_os.risk.repositories import InstrumentRiskProfileRepository, RiskPolicyRepository, RiskValidationRepository
from portfolio_os.risk.report_writer import RiskReportWriter
from portfolio_os.serialization import dumps_json
from portfolio_os.tickets import OrderTicketRepository, OrderTicketService
from portfolio_os.tickets.report_writer import OrderTicketReportWriter

RISK_REPORT_DIR = Path("data/exports/risk_reports")
ORDER_TICKET_REPORT_DIR = Path("data/exports/order_tickets")


def register_stage2_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("record-price")
    p.add_argument("--instrument-id", type=int, required=True)
    p.add_argument("--price-date", required=True)
    p.add_argument("--currency", required=True)
    p.add_argument("--price", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--source-ref")
    p.set_defaults(func=cmd_record_price)

    p = subparsers.add_parser("record-fx-rate")
    p.add_argument("--rate-date", required=True)
    p.add_argument("--base-currency", required=True)
    p.add_argument("--quote-currency", required=True)
    p.add_argument("--rate", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--source-ref")
    p.set_defaults(func=cmd_record_fx_rate)

    subparsers.add_parser("list-prices").set_defaults(func=cmd_list_prices)
    subparsers.add_parser("list-fx-rates").set_defaults(func=cmd_list_fx_rates)

    p = subparsers.add_parser("seed-default-risk-policy")
    p.add_argument("--base-currency", required=True)
    p.set_defaults(func=cmd_seed_default_risk_policy)

    p = subparsers.add_parser("create-risk-policy")
    p.add_argument("--name", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--base-currency", required=True)
    p.add_argument("--active", action="store_true")
    p.set_defaults(func=cmd_create_risk_policy)

    p = subparsers.add_parser("activate-risk-policy")
    p.add_argument("--policy-version-id", type=int, required=True)
    p.set_defaults(func=cmd_activate_risk_policy)

    p = subparsers.add_parser("add-risk-rule")
    p.add_argument("--policy-version-id", type=int, required=True)
    p.add_argument("--rule-code", required=True)
    p.add_argument("--threshold-value", required=True)
    p.add_argument("--threshold-unit", required=True, choices=["amount", "ratio", "count"])
    p.add_argument("--severity", required=True, choices=["hard_block", "adjust_down", "warn"])
    p.add_argument("--currency")
    p.set_defaults(func=cmd_add_risk_rule)

    subparsers.add_parser("list-risk-rules").set_defaults(func=cmd_list_risk_rules)

    p = subparsers.add_parser("set-instrument-risk-profile")
    p.add_argument("--instrument-id", type=int, required=True)
    p.add_argument("--risk-bucket", default="other")
    p.add_argument("--leveraged", action="store_true")
    p.add_argument("--crypto-related", action="store_true")
    p.add_argument("--single-name-equity", action="store_true")
    p.set_defaults(func=cmd_set_instrument_risk_profile)

    p = subparsers.add_parser("create-intent")
    p.add_argument("--account-id", type=int, required=True)
    p.add_argument("--instrument-id", type=int, required=True)
    p.add_argument("--side", choices=["buy", "sell"], required=True)
    p.add_argument("--currency", required=True)
    p.add_argument("--quantity")
    p.add_argument("--notional")
    p.add_argument("--limit-price")
    p.add_argument("--rationale")
    p.set_defaults(func=cmd_create_intent)

    p = subparsers.add_parser("validate-intent")
    p.add_argument("--intent-id", type=int, required=True)
    p.add_argument("--as-of-date", required=True)
    p.add_argument("--report-dir", type=Path, default=RISK_REPORT_DIR)
    p.set_defaults(func=cmd_validate_intent)

    p = subparsers.add_parser("show-risk-validation")
    p.add_argument("--risk-validation-id", type=int, required=True)
    p.set_defaults(func=cmd_show_risk_validation)

    p = subparsers.add_parser("create-order-ticket")
    p.add_argument("--risk-validation-id", type=int, required=True)
    p.add_argument("--expires-at")
    p.add_argument("--report-dir", type=Path, default=ORDER_TICKET_REPORT_DIR)
    p.set_defaults(func=cmd_create_order_ticket)

    p = subparsers.add_parser("show-order-ticket")
    p.add_argument("--order-ticket-id", type=int, required=True)
    p.set_defaults(func=cmd_show_order_ticket)

    p = subparsers.add_parser("approve-ticket")
    p.add_argument("--order-ticket-id", type=int, required=True)
    p.add_argument("--reason")
    p.set_defaults(func=cmd_approve_ticket)

    p = subparsers.add_parser("reject-ticket")
    p.add_argument("--order-ticket-id", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_reject_ticket)

    p = subparsers.add_parser("modify-ticket")
    p.add_argument("--order-ticket-id", type=int, required=True)
    p.add_argument("--quantity")
    p.add_argument("--notional")
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_modify_ticket)

    subparsers.add_parser("expire-tickets").set_defaults(func=cmd_expire_tickets)
    subparsers.add_parser("list-open-tickets").set_defaults(func=cmd_list_open_tickets)

    p = subparsers.add_parser("log-manual-execution")
    p.add_argument("--order-ticket-id", type=int)
    p.add_argument("--override-ticket-id", type=int)
    p.add_argument("--quantity", required=True)
    p.add_argument("--price", required=True)
    p.add_argument("--fee", default="0")
    p.add_argument("--tax", default="0")
    p.add_argument("--executed-at")
    p.add_argument("--broker-ref")
    p.set_defaults(func=cmd_log_manual_execution)

    subparsers.add_parser("list-pending-executions").set_defaults(func=cmd_list_pending_executions)

    p = subparsers.add_parser("confirm-executions-after-reconciliation")
    p.add_argument("--reconciliation-id", type=int, required=True)
    p.set_defaults(func=cmd_confirm_executions)

    p = subparsers.add_parser("declare-override")
    p.add_argument("--type", required=True)
    p.add_argument("--account-id", type=int, required=True)
    p.add_argument("--instrument-id", type=int)
    p.add_argument("--side", choices=["buy", "sell"])
    p.add_argument("--quantity")
    p.add_argument("--notional")
    p.add_argument("--currency")
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_declare_override)

    p = subparsers.add_parser("confirm-override")
    p.add_argument("--override-ticket-id", type=int, required=True)
    p.add_argument("--final-choice", required=True, choices=["execute", "cancel", "modify"])
    p.set_defaults(func=cmd_confirm_override)

    p = subparsers.add_parser("log-override-execution")
    p.add_argument("--override-ticket-id", type=int, required=True)
    p.add_argument("--quantity", required=True)
    p.add_argument("--price", required=True)
    p.add_argument("--fee", default="0")
    p.add_argument("--tax", default="0")
    p.add_argument("--executed-at")
    p.add_argument("--broker-ref")
    p.set_defaults(func=cmd_log_override_execution)

    subparsers.add_parser("list-overrides").set_defaults(func=cmd_list_overrides)

    p = subparsers.add_parser("record-postmortem")
    p.add_argument("--override-ticket-id", type=int)
    p.add_argument("--order-ticket-id", type=int)
    p.add_argument("--due-date", required=True)
    p.set_defaults(func=cmd_record_postmortem)

    subparsers.add_parser("list-journal").set_defaults(func=cmd_list_journal)


def _dt(text: str | None) -> datetime:
    if text:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    return datetime.now(timezone.utc).replace(microsecond=0)


def cmd_record_price(args):
    with Database(args.db) as db:
        print(dumps_json(PricingRepository(db).record_price(args.instrument_id, date.fromisoformat(args.price_date), args.currency, Decimal(args.price), args.source, args.source_ref)))
    return 0


def cmd_record_fx_rate(args):
    with Database(args.db) as db:
        print(dumps_json(PricingRepository(db).record_fx_rate(date.fromisoformat(args.rate_date), args.base_currency, args.quote_currency, Decimal(args.rate), args.source, args.source_ref)))
    return 0


def cmd_list_prices(args):
    with Database(args.db) as db:
        print(json.dumps(db.fetch_all("SELECT * FROM price_snapshots ORDER BY price_snapshot_id"), ensure_ascii=False))
    return 0


def cmd_list_fx_rates(args):
    with Database(args.db) as db:
        print(json.dumps(db.fetch_all("SELECT * FROM fx_rates ORDER BY fx_rate_id"), ensure_ascii=False))
    return 0


def cmd_seed_default_risk_policy(args):
    with Database(args.db) as db:
        print(dumps_json({"policy_version_id": seed_default_risk_policy(db, args.base_currency)}))
    return 0


def cmd_create_risk_policy(args):
    with Database(args.db) as db:
        print(dumps_json(RiskPolicyRepository(db).create_policy(args.name, args.version, args.base_currency, args.active)))
    return 0


def cmd_activate_risk_policy(args):
    with Database(args.db) as db:
        db.execute("UPDATE risk_policy_versions SET is_active = 0 WHERE is_active = 1")
        db.execute("UPDATE risk_policy_versions SET is_active = 1 WHERE policy_version_id = ?", (args.policy_version_id,))
        db.commit()
        print(dumps_json(RiskPolicyRepository(db).get_policy(args.policy_version_id)))
    return 0


def cmd_add_risk_rule(args):
    with Database(args.db) as db:
        rule = RiskRule(0, args.policy_version_id, args.rule_code, "global", Decimal(args.threshold_value), args.threshold_unit, args.severity, args.currency)
        print(dumps_json(RiskPolicyRepository(db).add_rule(rule)))
    return 0


def cmd_list_risk_rules(args):
    with Database(args.db) as db:
        policy = RiskPolicyRepository(db).active_policy()
        print(dumps_json(RiskPolicyRepository(db).list_rules(policy.policy_version_id) if policy else []))
    return 0


def cmd_set_instrument_risk_profile(args):
    with Database(args.db) as db:
        print(dumps_json(InstrumentRiskProfileRepository(db).set_profile(args.instrument_id, args.risk_bucket, args.leveraged, args.crypto_related, args.single_name_equity)))
    return 0


def cmd_create_intent(args):
    with Database(args.db) as db:
        intent = TransactionIntentService(db).create_intent(args.account_id, args.instrument_id, args.side, args.currency, Decimal(args.quantity) if args.quantity else None, Decimal(args.notional) if args.notional else None, Decimal(args.limit_price) if args.limit_price else None, args.rationale)
        print(dumps_json(intent))
    return 0


def cmd_validate_intent(args):
    with Database(args.db) as db:
        intent_repo = TransactionIntentRepository(db)
        intent = intent_repo.get(args.intent_id)
        ledger = LedgerSnapshotBuilder(db).build_snapshot(date.fromisoformat(args.as_of_date), intent.account_id)
        result = RiskEngine(db).validate_and_persist(intent, ledger, as_of_date=date.fromisoformat(args.as_of_date))
        intent_repo.update_status(intent.intent_id, {"passed": "risk_passed", "adjusted": "risk_adjusted", "rejected": "risk_rejected"}[result.validation_status])
        writer = RiskReportWriter()
        writer.write_markdown_report(result, args.report_dir / f"risk_validation_{result.risk_validation_id}.md")
        writer.write_json_report(result, args.report_dir / f"risk_validation_{result.risk_validation_id}.json")
        print(dumps_json(result))
    return 0


def cmd_show_risk_validation(args):
    with Database(args.db) as db:
        print(dumps_json(RiskValidationRepository(db).get(args.risk_validation_id)))
    return 0


def cmd_create_order_ticket(args):
    with Database(args.db) as db:
        expires_at = _dt(args.expires_at) if args.expires_at else datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=1)
        ticket = OrderTicketService(db).create_ticket_from_validation(args.risk_validation_id, expires_at)
        writer = OrderTicketReportWriter()
        writer.write_markdown_report(ticket, args.report_dir / f"order_ticket_{ticket.order_ticket_id}.md")
        writer.write_json_report(ticket, args.report_dir / f"order_ticket_{ticket.order_ticket_id}.json")
        print(dumps_json(ticket))
    return 0


def cmd_show_order_ticket(args):
    with Database(args.db) as db:
        print(dumps_json(OrderTicketRepository(db).get(args.order_ticket_id)))
    return 0


def cmd_approve_ticket(args):
    with Database(args.db) as db:
        ticket = OrderTicketService(db).approve_ticket(args.order_ticket_id, args.reason)
        print(dumps_json(ticket))
    return 0


def cmd_reject_ticket(args):
    with Database(args.db) as db:
        print(dumps_json(OrderTicketService(db).reject_ticket(args.order_ticket_id, args.reason)))
    return 0


def cmd_modify_ticket(args):
    with Database(args.db) as db:
        print(dumps_json(OrderTicketService(db).modify_ticket(args.order_ticket_id, Decimal(args.quantity) if args.quantity else None, Decimal(args.notional) if args.notional else None, args.reason)))
    return 0


def cmd_expire_tickets(args):
    with Database(args.db) as db:
        repo = OrderTicketRepository(db)
        count = 0
        now = datetime.now(timezone.utc)
        for ticket in repo.list_open():
            if ticket.expires_at < now:
                repo.update_status(ticket.order_ticket_id, "expired", "cancelled", "ticket expired")
                count += 1
        print(dumps_json({"expired": count}))
    return 0


def cmd_list_open_tickets(args):
    with Database(args.db) as db:
        print(dumps_json(OrderTicketRepository(db).list_open()))
    return 0


def cmd_log_manual_execution(args):
    with Database(args.db) as db:
        if args.order_ticket_id is None:
            raise SystemExit("--order-ticket-id is required; use log-override-execution for overrides")
        execution = ManualExecutionService(db).log_execution_for_ticket(args.order_ticket_id, Decimal(args.quantity), Decimal(args.price), Decimal(args.fee), Decimal(args.tax), _dt(args.executed_at), args.broker_ref)
        print(dumps_json(execution))
    return 0


def cmd_list_pending_executions(args):
    with Database(args.db) as db:
        print(dumps_json(ManualExecutionRepository(db).list_pending()))
    return 0


def cmd_confirm_executions(args):
    with Database(args.db) as db:
        print(dumps_json({"confirmed": ManualExecutionService(db).mark_reconciled_after_passed_reconciliation(args.reconciliation_id)}))
    return 0


def cmd_declare_override(args):
    with Database(args.db) as db:
        override = OverrideService(db).declare_override(args.type, args.account_id, args.instrument_id, args.side, Decimal(args.quantity) if args.quantity else None, Decimal(args.notional) if args.notional else None, args.currency, args.reason)
        print(dumps_json(override))
    return 0


def cmd_confirm_override(args):
    with Database(args.db) as db:
        print(dumps_json(OverrideService(db).confirm_override(args.override_ticket_id, args.final_choice)))
    return 0


def cmd_log_override_execution(args):
    with Database(args.db) as db:
        override = OverrideTicketRepository(db).get(args.override_ticket_id)
        execution = ManualExecutionService(db).log_execution_for_override(override, Decimal(args.quantity), Decimal(args.price), Decimal(args.fee), Decimal(args.tax), _dt(args.executed_at), args.broker_ref)
        print(dumps_json(execution))
    return 0


def cmd_list_overrides(args):
    with Database(args.db) as db:
        print(dumps_json(OverrideTicketRepository(db).list_open()))
    return 0


def cmd_record_postmortem(args):
    with Database(args.db) as db:
        print(dumps_json({"postmortem_task_id": PostmortemTaskRepository(db).schedule(date.fromisoformat(args.due_date), args.order_ticket_id, args.override_ticket_id)}))
    return 0


def cmd_list_journal(args):
    with Database(args.db) as db:
        print(json.dumps(DecisionJournalRepository(db).list(), ensure_ascii=False))
    return 0
