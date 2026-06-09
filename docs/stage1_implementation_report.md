# Stage 1 Implementation Report

## Verification Basis

This report checks the implemented Stage 1 code against:

- `프로젝트 바이블.md`
- `Portfolio_OS_Macro_Stage_Roadmap.md`
- `Portfolio_OS_Stage1_Ledger_Truth_Foundation_Tech_Spec.md`
- implemented code under `src/portfolio_os`
- migrations under `migrations`
- tests under `tests`

Existing root documents were not moved.

## Implemented

- Python package skeleton with `portfolio-os` CLI entrypoint.
- SQLite migration runner with `schema_migrations`.
- Required Stage 1 tables and indexes.
- Database connection pragmas for foreign keys, WAL, and busy timeout.
- Dataclass models for ledger, external snapshot, and reconciliation contracts.
- Validators for Decimal, currency, transactions, cash balances, liabilities, tax reserves, and external snapshots.
- Repository layer for Stage 1 tables.
- Ledger snapshot builder for positions, cash, liabilities, and tax reserves.
- External CSV snapshot importer that writes normalized JSON artifacts.
- Reconciliation service with default tolerances.
- Markdown and JSON reconciliation report writer.
- Ledger state machine.
- Unit and integration tests.

## Confirmed Boundaries

- No Stage 2+ functionality is implemented.
- No research agent is implemented.
- No senior memo layer is implemented.
- No macro layer is implemented.
- No risk-gated ticketing layer is implemented.
- No broker API execution is implemented.
- No Telegram or messenger automation is implemented.
- No RAG or model governance layer is implemented.

## Important Accounting Safeguards

- External snapshot cash is not inserted into `cash_balances`.
- `cash_balances` is OS internal anchor data only.
- External snapshots are normalized as JSON artifacts and used as actual values during reconciliation.
- Float values are rejected by validation.
- Buy transactions require positive quantity and negative `net_cash_amount`.
- Sell transactions require negative quantity and positive `net_cash_amount`.
- Negative fee and tax amounts are rejected.
- Voided transactions are excluded from snapshot calculations.
- Reconciliation pass is required before the ledger can become `reconciled`.

## Test Coverage Present

Current tests cover:

- schema and migration creation
- Decimal policy
- transaction validation
- external snapshot cash separation
- ambiguous instrument matching
- reconciliation pass
- cash diff failure
- broken to correction to reconciled recovery
- CLI `init-db` and `ledger-status` smoke checks

## Known Implementation Notes

- Runtime dependencies remain standard library only.
- `pytest` is the only development dependency declared.
- The default database path is `data/portfolio_os.sqlite3`.
- The default reconciliation report directory is `data/exports/reconciliation_reports/`.
