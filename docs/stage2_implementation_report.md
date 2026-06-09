# Portfolio OS Stage 2 Implementation Report

## Summary

Stage 2 implements the Risk-Gated Manual Operating Loop on top of the existing Stage 1 ledger foundation.

The implemented loop is:

```text
LedgerSnapshot
-> Transaction Intent
-> Risk Validation
-> Manual Order Ticket
-> Human Approval
-> Human Manual Execution Log
-> Stage 1 provisional transaction
-> Reconciliation confirmation
```

Stage 2 does not execute orders automatically and does not add Stage 3+ AI, research, macro, broker write, or UI functionality.

## Preserved Stage 1 Contracts

- Stage 1 migrations `001`-`008` were not modified.
- Existing root documents were not moved or modified.
- `cash_balances` remains internal OS cash anchor storage only.
- External snapshot values are not written into `cash_balances`.
- Decimal/no-float policy remains in force.
- Stage 2 consumes `LedgerSnapshotBuilder` and `LedgerStateMachine` rather than rebuilding ledger truth.

## Implemented Stage 2 Storage

New migrations `009`-`022` add:

- price snapshots
- FX rates
- instrument risk profiles
- risk policy versions
- risk rules
- transaction intents
- risk validation results
- order tickets
- order ticket events
- manual execution logs
- override tickets
- decision journal
- postmortem tasks
- Stage 2 indexes

## Approved Corrections Implemented

- `seed-default-risk-policy` accepts `--base-currency` and stores it in `risk_policy_versions.base_currency`.
- USD is not hardcoded into policy logic.
- Default seeded policy includes `TAX_RESERVE_PROTECTION=1.00`.
- Tax reserve cash is fully protected from buy capacity.
- `DEBT_EXPOSURE_CHECK` is implemented as:

```text
total_active_liabilities / gross_portfolio_value <= 0.50
```

- Manual executions are not blindly reconciled after a passed reconciliation.
- A manual execution is marked reconciled only when its linked `created_transaction_id` is confirmed.

## Implemented CLI Surface

Stage 2 adds CLI commands for:

- price and FX input
- default risk policy seeding
- risk rules and instrument risk profiles
- intent creation and validation
- order ticket creation, approval, rejection, modification, expiry, and listing
- manual execution logging and reconciliation confirmation
- override declaration and confirmation
- decision journal and postmortem task recording

All commands use the existing global `--db` option.

## Reports

Risk reports are generated under:

```text
data/exports/risk_reports/
```

Order ticket reports are generated under:

```text
data/exports/order_tickets/
```

## Verification

Latest test result:

```text
python -m pytest -> 22 passed
```

Coverage includes:

- Stage 2 migrations after Stage 1 migrations
- non-USD base currency risk policy seed
- ledger status gates
- tax reserve protection rule
- debt exposure rule path
- buy ticket flow
- manual execution creating provisional Stage 1 transaction
- selective execution reconciliation
- broken ledger official ticket block
- override declaration
- CLI smoke for default policy seed
