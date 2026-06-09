# Portfolio OS Stage 2 Handoff for Stage 3

## 1. Executive Summary

Stage 2 implemented the Risk-Gated Manual Operating Loop. In plain language, the system can now take a human trade intent, validate it against deterministic ledger-aware risk rules, create a manual order ticket, record human approval or rejection, log manual execution, create a provisional Stage 1 transaction, and later confirm execution only through reconciliation evidence.

- Current project root: `C:\Users\dahye\Documents\인생\자산`
- Python version target: Python `>=3.11`; verified locally with Python `3.13.2`
- SQLite DB path: `data/portfolio_os.sqlite3`
- CLI entrypoint: `portfolio-os` via `portfolio_os.cli.main:main`
- Dependency policy: standard-library runtime only; `pytest` is the only declared development dependency
- Current verification result: `python -m pytest -> 22 passed`
- Current generated reports:
  - `data/exports/risk_reports/risk_validation_1.md`
  - `data/exports/order_tickets/order_ticket_1.md`

Stage 2 still does not execute orders automatically. It records, constrains, and audits human manual trading behavior.

## 2. Stable Stage 2 Scope

Stage 2 is limited to:

- price snapshots
- FX rates
- instrument risk profiles
- risk policy versions
- risk rules
- transaction intents
- risk validation results
- manual order tickets
- order ticket events
- human approval, rejection, and modification
- manual execution logs
- override tickets
- decision journal
- postmortem tasks
- risk and ticket report generation

Stage 2 does not implement research, macro analysis, Senior memo generation, recommendation generation, broker write integration, or automatic execution.

## 3. Files and Directories Added

- `migrations/009_create_price_snapshots.sql` through `migrations/022_create_stage2_indexes.sql`: Stage 2 schema additions only.
- `src/portfolio_os/pricing/`: price and FX repository wrappers plus valuation helper.
- `src/portfolio_os/risk/`: Stage 2 models, default policy seed, action classification, deterministic risk engine, risk report writer, and risk repositories.
- `src/portfolio_os/intents/`: transaction intent repository, service, models wrapper, and validation helper.
- `src/portfolio_os/tickets/`: order ticket repository, service, report writer, and models wrapper.
- `src/portfolio_os/execution/`: manual execution repository, service, models wrapper, and execution sign validation helper.
- `src/portfolio_os/override/`: override ticket repository, service, models wrapper.
- `src/portfolio_os/journal/`: decision journal repository/service and postmortem task repository.
- `src/portfolio_os/cli/stage2_commands.py`: Stage 2 CLI command registration and handlers.
- `tests/unit/`: Stage 2 risk engine coverage was added alongside existing unit tests.
- `tests/integration/`: Stage 2 migration, flow, and CLI smoke tests were added.
- `data/exports/risk_reports/`: generated risk Markdown/JSON reports.
- `data/exports/order_tickets/`: generated order ticket Markdown/JSON reports.

Existing root documents were not moved or modified.

## 4. Database Tables Implemented

- `price_snapshots`: stores manual or CSV price references used by Stage 2 valuation and risk checks.
- `fx_rates`: stores manual or CSV exchange rates used for cross-currency validation.
- `instrument_risk_profiles`: stores deterministic risk bucket metadata for instruments.
- `risk_policy_versions`: stores versioned risk policies with a `base_currency` and active policy marker.
- `risk_rules`: stores policy thresholds such as cash reserve, buy limits, tax reserve protection, and debt exposure.
- `transaction_intents`: stores human trade intents before risk validation or ticket creation.
- `risk_validation_results`: stores immutable deterministic validation results with check details, failures, warnings, and approved adjusted values.
- `order_tickets`: stores validated manual order tickets and current ticket state.
- `order_ticket_events`: append-only event log for ticket state transitions.
- `manual_execution_logs`: stores human-entered execution facts linked to exactly one approved ticket or confirmed override.
- `override_tickets`: stores declared exceptions with human reason, risk warning, and confirmation state.
- `decision_journal`: append-only human decision record for ticket, override, and execution events.
- `postmortem_tasks`: stores scheduled postmortem tasks for later review.

Stage 3 can rely on these tables as Stage 2 operational audit records. Stage 3 should add new migrations for any schema changes.

## 5. Stable Stage 2 Invariants

- No automatic order execution.
- No risk validation, no official order ticket.
- No rejected validation, no order ticket.
- No expired validation, no order ticket.
- No human approval, no manual execution for official ticket.
- Manual execution must link to an approved ticket or human-confirmed override.
- Manual execution creates a Stage 1 transaction with `is_confirmed = 0`.
- Passed reconciliation confirms execution only when the linked `created_transaction_id` is confirmed.
- Risk-increasing official buy requires `ledger_status == reconciled`.
- Stale or provisional ledger status only allows risk-reducing official flow with warning.
- Broken ledger status blocks official ticket flow.
- Broken ledger status still allows correction or declared override.
- External snapshot values must not enter `cash_balances`.
- Float arithmetic remains forbidden by the Decimal policy.
- Historical transactions must not be directly mutated for accounting correction.
- Existing root documents remain untouched.

## 6. Risk Engine Behavior

Implemented entrypoint: `portfolio_os.risk.engine.RiskEngine`.

Action classification:

- `buy` is `risk_increasing`.
- `sell` is `risk_reducing` when holdings exist and remains subject to holding checks.
- `correction` and `override_precheck` are recognized intent sources.

Implemented checks:

- `LEDGER_STATUS_GATE`: risk-increasing official tickets require `reconciled`; broken blocks official tickets; stale/provisional risk-reducing flow produces warning.
- `PRICE_AVAILABLE`: buy/sell validation requires an active price snapshot.
- `FX_AVAILABLE`: cross-currency conversion uses `fx_rates`; missing FX rejects validation.
- `NO_MARKET_ORDER`: Stage 2 allows only limit order flow.
- `TAX_RESERVE_PROTECTION`: tax reserve cash is fully protected from buy capacity.
- `MIN_CASH_RESERVE`: buy validation preserves minimum cash.
- `DAILY_BUY_LIMIT`: adjustable buy notional limit.
- `WEEKLY_BUY_LIMIT`: adjustable buy notional limit.
- `MAX_ORDER_NOTIONAL`: adjustable single order notional limit.
- `MAX_ASSET_WEIGHT`: adjustable post-trade asset weight check.
- `MAX_BUCKET_WEIGHT`: implemented as Stage 2 MVP bucket approximation using post-trade asset weight.
- `DEBT_EXPOSURE_CHECK`: `total_active_liabilities / gross_portfolio_value <= 0.50`.
- `HOLDING_AVAILABLE_FOR_SELL`: sell quantity must not exceed current holding.

Risk result semantics:

- `passed`: all hard checks pass and no adjustment is needed.
- `adjusted`: requested size is too large, but a smaller size is allowed.
- `rejected`: non-adjustable gate fails, required data is missing, no valid adjusted size exists, or sell exceeds holdings.

Default seeded policy:

- Policy name/version: `stage2_default_policy v1.0.0`
- Base currency behavior: `seed-default-risk-policy --base-currency <CODE>` stores the selected code in `risk_policy_versions.base_currency`; USD is not hardcoded into policy logic.
- `MIN_CASH_RESERVE = 1000` in base currency
- `DAILY_BUY_LIMIT = 1000` in base currency
- `WEEKLY_BUY_LIMIT = 3000` in base currency
- `MAX_ORDER_NOTIONAL = 1000` in base currency
- `MAX_ASSET_WEIGHT = 0.25`
- `MAX_BUCKET_WEIGHT = 0.50`
- `TAX_RESERVE_PROTECTION = 1.00`
- `DEBT_EXPOSURE_CHECK = 0.50`

These are conservative local MVP defaults and are not investment advice.

## 7. Order Ticket Workflow

Implemented official flow:

1. `create-intent`: creates a `TransactionIntent`.
2. `validate-intent`: runs `RiskEngine`, persists `RiskValidationResult`, and writes a risk report.
3. `create-order-ticket`: creates an `OrderTicket` only from `passed` or `adjusted` validation.
4. `approve-ticket`: marks a validated ticket as approved and records a journal entry.
5. `reject-ticket`: marks a validated ticket as rejected and records a journal entry.
6. `modify-ticket`: marks the original ticket modified and creates a new intent.
7. `expire-tickets`: expires open tickets whose expiry has passed.
8. `log-manual-execution`: records manual execution for an approved ticket and creates a provisional Stage 1 transaction.
9. `confirm-executions-after-reconciliation`: confirms only linked executions whose Stage 1 transaction is confirmed after a passed reconciliation.

Ticket statuses:

```text
validated
approved
rejected
modified
expired
executed_provisional
reconciled
broken
cancelled
```

Ticket state changes are recorded in `order_ticket_events`.

## 8. Manual Execution Behavior

Approved ticket execution:

- `ManualExecutionService.log_execution_for_ticket` requires `order_tickets.status == approved`.
- It records the fill quantity, price, fees, tax, timestamp, and optional broker reference.
- It creates a Stage 1 `transactions` row with `is_confirmed = 0`.

Override execution:

- `ManualExecutionService.log_execution_for_override` requires `override_tickets.status == human_confirmed`.
- The override must have instrument, side, and currency before execution can be logged.

Transaction sign convention:

- Buy execution creates positive quantity and negative `net_cash_amount`.
- Sell execution creates negative quantity and positive `net_cash_amount`.
- Fees and taxes are included in `net_cash_amount`.

Execution statuses:

```text
logged
transaction_created
pending_reconciliation
reconciled
reconciliation_failed
voided
```

Implemented reconciliation confirmation:

- `mark_reconciled_after_passed_reconciliation` checks the latest passed reconciliation ID.
- It only marks an execution reconciled if its linked `created_transaction_id` is already confirmed.
- It does not blindly reconcile all pending executions after a passed reconciliation.

Failure status support exists in `ManualExecutionRepository.mark_failed`, but automatic failed-execution marking is not wired into the CLI confirmation path yet.

## 9. Override Behavior

Overrides can be declared when official ticket flow is blocked or bypassed. They are not official risk-validated tickets.

Implemented behavior:

- `declare-override` requires a human reason.
- It records current ledger status through `LedgerStateMachine`.
- It stores a risk warning explaining that the override is outside official risk validation.
- It sets reconciliation and postmortem due dates.
- `confirm-override` records the human final choice.
- `log-override-execution` can log execution only after human confirmation.

Postmortem behavior:

- Override rows store `mandatory_postmortem_date`.
- `record-postmortem` can create a `postmortem_tasks` row.
- Automatic postmortem task creation during override declaration is not currently wired; the task creation path is explicit through CLI/service.

## 10. Decision Journal and Postmortem

Decision journal behavior:

- `decision_journal` is append-only.
- Ticket approval, rejection, modification, override declaration/confirmation, and manual execution logging can be recorded.
- Journal rows store decision type, linked ticket/override/risk/execution IDs, reason, optional emotional state, and JSON context.

Postmortem behavior:

- `postmortem_tasks` stores due date, status, prompt questions, and optional completed journal decision.
- The implemented CLI can schedule postmortem tasks through `record-postmortem`.

Export/report behavior:

- Risk validations and order tickets have dedicated Markdown/JSON report writers.
- Journal export is currently a CLI list operation, not a dedicated file export.

## 11. CLI Commands Available

All Stage 2 commands support the global `--db` option through the main `portfolio-os` parser.

Price and FX:

- `record-price`: record a price snapshot.
- `record-fx-rate`: record an FX rate.
- `list-prices`: list price snapshots.
- `list-fx-rates`: list FX rates.

Risk policy:

- `seed-default-risk-policy`: seed `stage2_default_policy v1.0.0` with `--base-currency`.
- `create-risk-policy`: create a policy version.
- `activate-risk-policy`: activate a policy version.
- `add-risk-rule`: add a risk rule.
- `list-risk-rules`: list active policy rules.
- `set-instrument-risk-profile`: set instrument risk metadata.

Intent and validation:

- `create-intent`: create a transaction intent.
- `validate-intent`: run risk validation and generate reports.
- `show-risk-validation`: show a persisted risk validation.

Order ticket workflow:

- `create-order-ticket`: create a ticket from passed/adjusted validation and generate reports.
- `show-order-ticket`: show ticket details.
- `approve-ticket`: approve a validated ticket.
- `reject-ticket`: reject a validated ticket.
- `modify-ticket`: mark ticket modified and create a new intent.
- `expire-tickets`: expire overdue tickets.
- `list-open-tickets`: list open tickets.

Manual execution:

- `log-manual-execution`: log execution for approved official ticket.
- `list-pending-executions`: list pending manual executions.
- `confirm-executions-after-reconciliation`: confirm linked executions after passed reconciliation evidence.

Override and journal:

- `declare-override`: create a declared override with human reason.
- `confirm-override`: confirm/cancel/modify override final choice.
- `log-override-execution`: log execution for human-confirmed override.
- `list-overrides`: list open overrides.
- `record-postmortem`: schedule postmortem task.
- `list-journal`: list decision journal rows.

## 12. Reports Generated

Risk reports:

```text
data/exports/risk_reports/risk_validation_<id>.md
data/exports/risk_reports/risk_validation_<id>.json
```

Order ticket reports:

```text
data/exports/order_tickets/order_ticket_<id>.md
data/exports/order_tickets/order_ticket_<id>.json
```

Current generated reports:

- `data/exports/risk_reports/risk_validation_1.md`
- `data/exports/order_tickets/order_ticket_1.md`

`risk_validation_1.md` proves that Stage 2 can run a deterministic risk validation and write a human-readable report in the expected directory.

`order_ticket_1.md` proves that Stage 2 can create a manual order ticket from a valid risk validation and write execution instructions without executing the order.

## 13. Test Coverage

Verification:

```text
python -m pytest -> 22 passed
python -m compileall src tests -> passed
```

Unit coverage themes:

- Decimal float rejection remains intact.
- Stage 2 default policy base currency and tax reserve rule.
- ledger gate behavior for stale buy and stale reduce-only sell.
- risk engine rejection paths.

Integration coverage themes:

- Stage 2 migrations apply after Stage 1 migrations.
- non-USD default risk policy seed.
- buy ticket approval and execution flow.
- manual execution creates provisional Stage 1 transaction.
- selective execution reconciliation using linked confirmed transaction.
- broken ledger blocks official ticket while allowing override declaration.
- Stage 2 CLI smoke for default policy seed.

CLI smoke result:

- A full sample CLI flow created a passed risk validation, an approved ticket, and a pending manual execution.
- It generated the current risk and ticket Markdown reports.

## 14. Known Limitations

Stage 2 intentionally does not implement:

- UI
- automatic order execution
- broker write integration
- Stage 3 research layer
- macro layer
- Senior memo layer
- recommendation generation
- AI agent layer
- real personal financial data

Additional implementation limitations to preserve awareness:

- `MAX_BUCKET_WEIGHT` currently uses a Stage 2 MVP approximation rather than a full portfolio bucket valuation model.
- Failed reconciliation does not automatically mark pending executions as `reconciliation_failed` through the CLI path.
- Postmortem task creation is explicit through `record-postmortem`; override declaration records due dates but does not auto-create a postmortem task row.

## 15. Stage 3 Entry Contract

Stage 3 must treat the following as stable read inputs:

- Stage 1 `LedgerSnapshot` and `ledger_status`
- Stage 2 `RiskValidationResult`
- Stage 2 `OrderTicket`
- Stage 2 `ManualExecutionLog`
- Stage 2 `OverrideTicket`
- Stage 2 `decision_journal`
- Stage 2 `InstrumentRiskProfile`
- Stage 2 price and FX snapshots
- Stage 2 risk reports and ticket reports

Stage 3 should consume these objects rather than rebuilding trading truth, risk truth, or ledger truth independently.

## 16. Stage 3 Must Not Break

- Do not create recommendations that bypass `ledger_status`.
- Do not create action drafts that bypass risk validation.
- Do not mutate order tickets or transactions directly.
- Do not write external snapshot values into `cash_balances`.
- Do not introduce automatic execution.
- Do not treat research as order authority.
- Do not treat macro context as permission to bypass risk rules.
- Do not move existing root documents.
- Do not modify Stage 1 or Stage 2 migrations without new migrations.

Stage 3 must remain advisory or context-building unless a later explicit stage changes the operating contract.

## 17. Recommended Stage 3 Starting Point

Stage 3 should begin from read-only research support:

- fact-only research packet
- mandatory anti-thesis section
- source list
- missing data flags
- no buy/sell recommendation language
- macro context preparation only if included in Stage 3 scope
- Stage 1 ledger context as read-only input
- Stage 2 risk, ticket, execution, override, and journal context as read-only inputs

The Stage 3 Tech Spec should define how research context informs later human review without becoming order authority.
