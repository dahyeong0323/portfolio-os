# Stage 1: Ledger Truth Foundation

Stage 1 creates the official ledger foundation for Portfolio OS. It is intentionally not an AI or trading layer.

## Objective

Stage 1 reconstructs account positions, cash, liabilities, tax reserves, and transaction history inside one official ledger, then compares that ledger against external account snapshots.

## Implemented Components

- Account master: `accounts`
- Instrument master: `instruments`
- Transaction ledger: `transactions`
- Internal cash anchors: `cash_balances`
- Liabilities: `liabilities`
- Tax reserves: `tax_reserves`
- Reconciliation history: `reconciliation_snapshots`
- Migration history: `schema_migrations`

## Snapshot Builder Behavior

The snapshot builder creates a `LedgerSnapshot` for a target date.

- Positions are built from non-voided transactions.
- Buy quantity is positive.
- Sell quantity is negative.
- Zero positions are omitted from the snapshot.
- Cash is built from the latest internal cash anchor for each account/currency plus later transaction cash movements.
- If no cash anchor exists, cash is built from transaction cash movement only.
- Liabilities are selected as the latest active record per `account_id + liability_name + liability_type + currency`.
- Tax reserves are selected as the latest active record per `account_id + tax_year + tax_type + currency`.

## External Snapshot Boundary

External account snapshots are actual values used for reconciliation. They are not OS ledger facts.

- External CSV data is normalized into JSON artifacts under `data/imports/account_snapshots/`.
- External cash is not inserted into `cash_balances`.
- `cash_balances` stores only OS internal cash anchors.
- A passed reconciliation may mark related internal cash anchors as reconciled.

## Completion Evidence

The implementation includes tests for:

- SQLite schema initialization.
- Decimal policy.
- cash anchor and transaction-derived cash.
- external snapshot separation from `cash_balances`.
- reconciliation pass and failure.
- broken to correction/recovery flow.
- CLI smoke paths.
