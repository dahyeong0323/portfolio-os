# Portfolio OS

Ledger-first personal portfolio operating system with Stage 1 through Stage 5 domain workflows and a FastAPI adapter for frontend development stages.

This stage implements only the accounting foundation:

- SQLite ledger schema and migrations
- Decimal-only money, quantity, price, fee, tax, and FX handling
- append-only transaction records with void/reversal/correction paths
- internal cash anchors separated from external account snapshots
- ledger snapshot generation
- reconciliation against normalized external snapshots
- ledger status state machine
- `argparse` based `portfolio-os` CLI

The Stage 1 through Stage 5 domain and CLI layers remain standard-library based. The frontend API layer adds FastAPI, Pydantic, and Uvicorn. Development tests use pytest and HTTPX.

## Quick Start

```powershell
python -m pip install -e ".[dev]"
python -m portfolio_os.cli.main init-db
python -m portfolio_os.cli.main ledger-status
python -m uvicorn portfolio_os.api.app:app --reload
```

The default database path is `data/portfolio_os.sqlite3`.

External account snapshots are never inserted directly into `cash_balances`.
They are normalized into JSON artifacts and used as reconciliation actuals.

The API exposes the original read-only dashboard routes plus controlled frontend workflows for reconciliation, the risk-gated manual operating loop, human approval/manual execution logging, reconciliation confirmation for pending manual executions, and explicit override/audit-memory recording. It reuses the existing services, repositories, ledger builder, reconciliation service, Risk Engine, ticket service, manual execution service, override service, journal repositories, state machine, and SQLite database. See `docs/frontend/stage7_override_journal_api_contract.md` for the current frontend write boundary.

## Mission Control Frontend

Frontend Stage 7 adds override declaration, decision journal views, and scheduled postmortem task views to the React Mission Control at `frontend/`. It does not add broker integration, automatic trading, override execution logging, or postmortem completion recording. Run the API first, then start Vite:

```powershell
python -m uvicorn portfolio_os.api.app:app --reload
cd frontend
npm.cmd install
npm.cmd run dev
```

See `frontend/README.md` for workflow scope, mock mode, routes, and verification commands.
