# Portfolio OS Architecture

Portfolio OS Stage 1 is a ledger-first accounting foundation. The implemented system follows the project bible principle that the ledger comes before research, recommendations, risk memos, or execution automation.

## Implemented Boundary

Stage 1 implements only:

- SQLite storage and schema migrations
- account and instrument masters
- append-only transactions
- internal cash balance anchors
- liabilities and tax reserves
- ledger snapshot generation
- external snapshot import as normalized JSON artifacts
- reconciliation between OS ledger expected values and external actual values
- ledger status state machine
- Markdown and JSON reconciliation reports
- `argparse` CLI

Stage 1 does not implement research agents, senior memos, macro analysis, risk-gated order tickets, Telegram, broker API execution, RAG, or automated trading.

## Runtime Shape

The code is organized under `src/portfolio_os`:

- `db`: SQLite connection, pragma setup, and migration runner.
- `models`: immutable dataclass contracts for accounts, instruments, ledger snapshots, external snapshots, and reconciliation results.
- `validators`: Decimal, currency, date, and domain validation.
- `repositories`: database access for the Stage 1 tables.
- `ledger`: snapshot builder for positions, cash, liabilities, and tax reserves.
- `importers`: CSV-to-normalized-external-snapshot artifact import.
- `reconciliation`: comparison service and report writer.
- `state`: ledger status state machine.
- `cli`: `portfolio-os` command implementation.

## Data Flow

1. Migrations initialize the SQLite database.
2. The user records OS ledger facts: accounts, instruments, transactions, cash anchors, liabilities, and tax reserves.
3. External account snapshot CSV files are imported into normalized JSON artifacts.
4. The snapshot builder constructs expected OS ledger state for an `as_of_date`.
5. The reconciliation service compares expected values with external actual values.
6. Reconciliation results are persisted and exported as Markdown and JSON reports.
7. Ledger status is inferred from the latest reconciliation result and unreconciled inputs.

## Accounting Safeguards

- Money, quantity, price, fee, tax, and FX values are handled with `Decimal`.
- Float inputs are rejected by validation.
- Historical transactions are not directly edited for correction; void, reversal, and correction flows are used.
- External snapshot cash is not inserted into `cash_balances`.
- `cash_balances` is reserved for OS internal cash anchors.
- A `reconciled` status requires a passed reconciliation snapshot.
