# Portfolio OS Stage 1

Ledger Truth Foundation for a personal portfolio operating system.

This stage implements only the accounting foundation:

- SQLite ledger schema and migrations
- Decimal-only money, quantity, price, fee, tax, and FX handling
- append-only transaction records with void/reversal/correction paths
- internal cash anchors separated from external account snapshots
- ledger snapshot generation
- reconciliation against normalized external snapshots
- ledger status state machine
- `argparse` based `portfolio-os` CLI

Runtime dependencies are intentionally limited to the Python standard library.
`pytest` is used only for development tests.

## Quick Start

```powershell
python -m portfolio_os.cli.main init-db
python -m portfolio_os.cli.main ledger-status
```

The default database path is `data/portfolio_os.sqlite3`.

External account snapshots are never inserted directly into `cash_balances`.
They are normalized into JSON artifacts and used as reconciliation actuals.
