# Portfolio OS

Local Mission Control for personal portfolio operations.

## Overview

Portfolio OS is a local portfolio operating system for disciplined personal investment operations. It separates ledger truth, risk validation, human approval, manual execution logging, reconciliation evidence, override records, reports, and context layers into one auditable workflow.

It is not an automatic trading app. Portfolio OS does not place broker orders, does not expose a broker write API, and does not automate trade execution. It is designed to help a human operator understand portfolio state, validate intent, record decisions, and confirm activity against reconciliation evidence.

## Why I Built This

Personal investing often mixes thesis notes, trade ideas, execution records, broker exports, and portfolio state across scattered tools. That makes it hard to know which record has authority and which action is only supporting context.

Portfolio OS forces separation of authority:

- ledger truth
- risk engine
- human approval
- manual execution
- reconciliation
- audit memory

The project is a way to design a disciplined investment workflow, not a trading shortcut. It treats portfolio operation as a system of gates, records, and reviews rather than a single buy/sell interface.

## What It Does

- Ledger and account state dashboard
- External CSV reconciliation workflow
- Intent -> Risk Engine -> Order Ticket workflow
- Human approval and rejection
- Manual execution logging after external broker execution
- Reconciliation confirmation
- Override declaration and decision journal
- Postmortem task visibility
- Reports Center
- Research / Macro / Senior Memo / Governance read-only explorers
- System Boundaries page

## What It Does Not Do

- No automatic trading
- No broker write API
- No order placement
- No frontend SQLite access
- No CLI subprocess from frontend
- No hidden risk bypass
- No HTML execution for report/context content
- No authentication/RBAC yet
- No real desktop packaging yet

## Architecture

```text
React + TypeScript + Vite
        |
        v
FastAPI /api/v1
        |
        v
Portfolio OS domain services
        |
        v
SQLite ledger and audit database
```

React never reads SQLite directly. The frontend talks to FastAPI through `/api/v1` routes and uses TanStack Query for data fetching and mutation state.

FastAPI wraps the existing Portfolio OS domain services. GET endpoints are read-only where applicable, while mutation endpoints are scoped to controlled workflows such as reconciliation runs, intent validation, ticket approval, manual execution logging, reconciliation confirmation, and override decisions.

Reports use opaque server-generated references. The API resolves those references through a report registry and only serves supported Markdown/JSON artifacts from known directories.

## Authority Model

```text
Ledger Truth
    -> Risk Engine
    -> Human Approval
    -> Manual Execution Logging
    -> Reconciliation Evidence
    -> Audit Memory
```

Ledger truth comes from Stage 1 ledger and reconciliation state. The Risk Engine is the official risk authority for order tickets. Human approval is required before manual execution logging. Manual execution logging records an external broker action already performed by a human. Reconciliation evidence is required before confirmation.

Research, Macro, Senior Memo, and Governance surfaces are context only. Reports are audit/review material, not order authority. Overrides are declared exceptions, not official Risk Engine validation.

## Frontend Roadmap Completed

1. Read-only FastAPI API
2. Mission Control Dashboard
3. Reconciliation Workflow
4. Intent / Risk / Ticket Creation
5. Approval / Manual Execution Logging
6. Reconciliation Confirmation
7. Override / Journal / Postmortem
8. Reports Center
9. Research / Macro / Senior / Governance Explorer
10. Final Hardening / System Boundaries / Desktop Packaging Readiness

## Screenshots

Screenshots will be added after local demo capture.

![Dashboard](docs/assets/screenshots/dashboard.png)
![Reconciliation](docs/assets/screenshots/reconciliation.png)
![Risk Workspace](docs/assets/screenshots/risk-workspace.png)
![Ticket Detail](docs/assets/screenshots/ticket-detail.png)
![Executions](docs/assets/screenshots/executions.png)
![Reports Center](docs/assets/screenshots/reports-center.png)
![Governance / System Boundaries](docs/assets/screenshots/governance-system-boundaries.png)

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- React
- TypeScript
- Vite
- TanStack Query
- Vitest
- Pytest

## Local Setup

Start the backend from the repository root:

```powershell
python -m pip install -e ".[dev]"
python -m portfolio_os.cli.main init-db
python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The frontend runs at:

```text
http://127.0.0.1:5173
```

The API runs at:

```text
http://127.0.0.1:8000
```

Vite proxies `/api` to FastAPI during local development.

## QA Status

- Final QA Status: PASS
- Backend: 105 passed, 1 warning
- Frontend: 46 passed
- Production build: PASS
- Known warning: Starlette/python_multipart pending deprecation warning
- Safety search passed:
  - no frontend SQLite access
  - no CLI subprocess
  - no broker write
  - no direct-trade CTA strings
  - no `dangerouslySetInnerHTML` / `innerHTML` usage

See [Portfolio OS Final QA & Code Structure](docs/Portfolio_OS_Final_QA_and_Code_Structure.md).

## Known Limitations

- No authentication/RBAC
- No broker integration
- No automatic trading
- No ticket modification flow
- No override execution logging
- No postmortem completion recording
- No persistent audit export UI
- No Tauri scaffold

## Future v2 Direction

- Authentication/RBAC
- Persistent audit export
- Desktop packaging
- Broker read-only import first, never broker write by default
- Better screenshots/demo dataset
- Optional production deployment after security design

## Repository Status

- Version: v1.5 Mission Control MVP
- Tag: `v1.5-mission-control-mvp`
