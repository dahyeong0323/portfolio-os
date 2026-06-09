# Portfolio OS Stage 1 Handoff for Stage 2

## 1. Executive Summary

Stage 1 implemented the Ledger Truth Foundation: a local accounting layer that records internal portfolio facts, builds ledger snapshots, imports external account snapshots as actual values, reconciles expected vs actual state, and reports the resulting ledger status.

- Current project root: `C:\Users\dahye\Documents\인생\자산`
- Python version target: Python `>=3.11`; verified locally with Python `3.13.2`
- SQLite DB path: `data/portfolio_os.sqlite3`
- CLI entrypoint: `portfolio-os` via `portfolio_os.cli.main:main`
- Dependency policy: standard-library runtime only; `pytest` is the only declared development dependency

Stage 1 does not implement order tickets, risk validation, human approval workflow, decision journal, override system, broker execution, UI, or AI decision layers.

## 2. Stable Stage 1 Scope

Stage 1 is limited to:

- accounts
- instruments
- transactions
- cash balances
- liabilities
- tax reserves
- reconciliation snapshots
- external snapshot import
- ledger status calculation
- reconciliation report generation

The implemented system answers whether the OS ledger matches an external account snapshot as of a specific date.

## 3. Files and Directories Added

- `migrations/`: SQL migrations for Stage 1 tables, indexes, and migration history.
- `src/portfolio_os/db/`: SQLite connection wrapper, pragma setup, and migration runner.
- `src/portfolio_os/models/`: dataclass contracts for accounts, instruments, transactions, snapshots, reconciliation results, and status literals.
- `src/portfolio_os/repositories/`: repository layer for Stage 1 table access and persistence.
- `src/portfolio_os/validators/`: Decimal, currency, date, transaction, cash, liability, tax reserve, and external snapshot validation.
- `src/portfolio_os/ledger/`: `LedgerSnapshotBuilder` for expected ledger state.
- `src/portfolio_os/reconciliation/`: reconciliation comparison service and Markdown/JSON report writer.
- `src/portfolio_os/state/`: `LedgerStateMachine` and stale/provisional/broken/reconciled status logic.
- `src/portfolio_os/importers/`: CSV external snapshot importer and normalized JSON artifact read/write helpers.
- `src/portfolio_os/cli/`: `argparse` CLI implementation.
- `tests/unit/`: focused validation, Decimal, transaction, and matching tests.
- `tests/integration/`: schema, reconciliation flow, recovery, external snapshot boundary, and CLI smoke tests.
- `data/imports/`: default import area, including external account snapshot artifacts.
- `data/exports/reconciliation_reports/`: default reconciliation Markdown/JSON report output area.

## 4. Database Tables Implemented

- `accounts`: account master records. Stage 2 can rely on stable account IDs, active flags, account type, institution, and base currency.
- `instruments`: instrument master records. Stage 2 can rely on stable instrument IDs and `symbol + exchange + currency` uniqueness.
- `transactions`: append-only transaction ledger. Stage 2 must treat this as the source of position and transaction cash movement.
- `cash_balances`: OS internal cash anchors only. Stage 2 must not treat external cash snapshots as eligible rows here.
- `liabilities`: dated liability records. The ledger snapshot uses latest active scoped records.
- `tax_reserves`: dated protected tax reserve records. The ledger snapshot uses latest active scoped records.
- `reconciliation_snapshots`: persisted reconciliation results with serialized expected, actual, and diff payloads.
- `schema_migrations`: migration history with `version`, `name`, `applied_at`, and `checksum`.

The implementation uses SQL migrations rather than ad hoc table creation.

## 5. Stable Data Invariants

- All money, quantity, price, fee, tax, and FX values use Python `Decimal`.
- Float input is rejected by validation.
- Decimal values are stored as text-preserving strings in `DECIMAL_TEXT` columns and parsed back into `Decimal`.
- Historical transactions are append-only from the accounting perspective.
- Corrections use void, reversal, or correction flows.
- External snapshot cash must never be inserted directly into `cash_balances`.
- `cash_balances` is only for internal OS cash anchors.
- External snapshots are stored as normalized JSON artifacts.
- Reconciliation `passed` is required before ledger status can become `reconciled`.
- Buy transactions use positive quantity and negative `net_cash_amount`.
- Sell transactions use negative quantity and positive `net_cash_amount`.
- Deposit, dividend, interest, and transfer-in cash movements must not be negative.
- Withdrawal, fee, tax, and transfer-out cash movements must not be positive.
- Fee and tax amounts cannot be negative.
- Voided transactions require `void_reason` and are excluded from ledger snapshot calculations.

## 6. Ledger Snapshot Behavior

`LedgerSnapshotBuilder` builds expected OS ledger state for an `as_of_date`.

- Positions: summed from non-voided signed transactions grouped by `account_id + instrument_id`; zero positions are omitted.
- Cash: latest internal cash anchor per `account_id + currency`, plus later transaction `net_cash_amount`; if no anchor exists, transaction cash movement starts from zero.
- Liabilities: latest active scoped record per `account_id + liability_name + liability_type + currency`.
- Tax reserves: latest active scoped record per `account_id + tax_year + tax_type + currency`.

The builder returns a `LedgerSnapshot` with positions, cash, liabilities, tax reserves, generated timestamp, and current ledger status.

## 7. External Snapshot Import Behavior

External snapshot artifacts are written under `data/imports/account_snapshots/` by default.

Stored metadata includes:

- artifact schema name
- snapshot `as_of_date`
- snapshot `source`
- positions
- cash
- liabilities
- tax reserves
- `received_at`

No checksum is currently stored for external snapshot artifacts. Checksums are implemented for SQL migrations only.

Position matching behavior:

- If `instrument_id` is supplied, it must exist and match `symbol`, `currency`, and optional `exchange`.
- If `instrument_id` is absent, the importer searches instruments by `symbol + currency + exchange`.
- Exactly one match is accepted.
- Zero matches become `missing`.
- Multiple matches become `ambiguous`.
- Missing or ambiguous matches are not silently passed; reconciliation becomes `needs_review` with ledger status `broken`.

External snapshot values are actual values only. They must not become internal ledger anchors before reconciliation, because that would make reconciliation compare the external snapshot against itself.

## 8. Reconciliation Behavior

Input:

- expected values from `LedgerSnapshotBuilder`
- actual values from a normalized `ExternalAccountSnapshot`
- `ReconciliationTolerance`

Output:

- `ReconciliationResult`
- persisted `reconciliation_snapshots` row
- Markdown and JSON reports

Default tolerances:

- cash: `1.00`
- quantity: `0.000001`
- liability: `1.00`
- tax reserve: `1.00`

Result rules:

- `passed` / `reconciled`: all over-tolerance diff counts are zero and all instrument matches are resolved.
- `failed` / `broken`: at least one diff exceeds tolerance.
- `needs_review` / `broken`: required instrument matching is missing, invalid, or ambiguous.

Reports are generated under `data/exports/reconciliation_reports/`.

The generated `data/exports/reconciliation_reports/reconciliation_1.md` proves that the implemented CLI can run a sample Stage 1 reconciliation and produce a Markdown report in the expected export directory.

## 9. Ledger State Machine

Implemented statuses:

- `provisional`
- `reconciled`
- `stale`
- `broken`

Implemented transitions and status rules:

- Initial state with no reconciliation history is `provisional`.
- New unconfirmed transaction input makes the ledger `provisional`.
- New unreconciled internal cash anchor makes the ledger `provisional`.
- Passed reconciliation can produce `reconciled`.
- Over-tolerance reconciliation differences produce `broken`.
- Missing or ambiguous required instrument matching produces `broken`.
- A broken ledger stays `broken` over time.
- Stale threshold is 7 days after the latest reconciliation.
- Correction or reversal input can move a broken ledger back to `provisional`, but another passed reconciliation is required to return to `reconciled`.

## 10. CLI Commands Available

All commands are implemented under the `portfolio-os` CLI and support the global `--db` option.

- `init-db`: initialize the SQLite database and apply migrations.
- `add-account`: create an account master record.
- `add-instrument`: create an instrument master record.
- `record-transaction`: record a transaction ledger row.
- `record-cash-balance`: record an internal OS cash anchor.
- `record-liability`: record a liability row.
- `record-tax-reserve`: record a tax reserve row.
- `import-external-snapshot`: import CSV snapshot files into a normalized JSON artifact.
- `run-reconciliation`: build the ledger snapshot, compare it to an external snapshot artifact, persist the result, and write reports.
- `ledger-status`: print the current ledger status.
- `export-reconciliation-report`: export the latest raw reconciliation snapshot row as JSON.

## 11. Test Coverage

Latest verification:

```text
python -m pytest -> 13 passed
```

Unit coverage themes:

- Decimal policy and float rejection
- transaction validation
- buy/sell cash sign convention
- negative fee/tax rejection
- external snapshot cash rejection from `cash_balances`
- missing/ambiguous instrument matching behavior

Integration coverage themes:

- schema and migration creation
- account, instrument, transaction, cash, liability, and tax reserve flow
- ledger snapshot generation
- reconciliation pass case
- reconciliation cash diff failed/broken case
- broken to correction to reconciled recovery
- external snapshot artifact boundary
- CLI `init-db` and `ledger-status` smoke check

CLI reconciliation smoke was also verified with sample data and produced `reconciled` after a passed reconciliation.

## 12. Known Limitations

Stage 1 intentionally does not implement:

- UI
- automatic order execution
- Stage 2 operating loop
- order tickets
- human approval workflow
- decision journal
- override system
- portfolio risk validation
- external write integration
- real personal financial data

The current implementation is a local Stage 1 ledger foundation only.

## 13. Stage 2 Entry Contract

Stage 2 should treat the following as stable Stage 1 contracts:

- DB connection layer and pragmas
- migration system and `schema_migrations`
- Decimal policy and float rejection
- account repository
- instrument repository
- transaction repository
- cash balance repository as internal-anchor storage
- ledger snapshot builder
- reconciliation service
- ledger status semantics
- external snapshot import boundary
- report export path: `data/exports/reconciliation_reports/`

Stage 2 should consume `LedgerSnapshot` and `ledger_status` rather than rebuilding ledger truth independently.

## 14. Stage 2 Must Not Break

- Do not write external snapshot values into `cash_balances`.
- Do not bypass reconciliation before using `reconciled` status.
- Do not mutate historical transactions directly.
- Do not introduce float arithmetic.
- Do not create order or risk logic that ignores `ledger_status`.
- Do not modify Stage 1 schema without a migration.
- Do not move existing root documents.
- Do not treat external snapshot artifacts as internal ledger facts.

## 15. Recommended Stage 2 Starting Point

Stage 2 should begin from the Stage 1 ledger boundary, without changing it.

Recommended design starting points:

- validated manual order ticket
- risk pre-check based on `LedgerSnapshot`
- transaction intent model
- order status model
- human approval state
- provisional execution log
- later reconciliation confirmation

The first Stage 2 tech spec should define how a proposed action is checked against the current ledger status and snapshot, how a human approves or rejects it, and how any eventual manual execution is logged before final reconciliation.
