# Portfolio OS Mission Control

Local React Mission Control frontend for Portfolio OS.

Portfolio OS is not an automatic trading system. The UI reads from FastAPI, uses existing Portfolio OS services/repositories, and preserves the ledger, Risk Engine, manual approval, reconciliation, override, reporting, and context boundaries built through Stages 1-10.

## Run Locally

Start the backend from the repository root:

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Vite serves `http://127.0.0.1:5173` and proxies `/api` to `http://127.0.0.1:8000`.

## Routes

- `/`: Mission Control dashboard
- `/ledger`: accounts, instruments, and ledger snapshot
- `/reconciliation`: snapshot import, reconciliation run, differences, and report
- `/risk`: intent creation, Risk Engine validation, and official ticket creation
- `/tickets`: order ticket register
- `/tickets/:ticketId`: ticket detail, approval/rejection, and manual execution logging when allowed
- `/executions`: pending manual executions and reconciliation confirmation
- `/overrides`: override register and explicit exception declaration
- `/overrides/:overrideId`: override detail, linked journal, and linked postmortem task
- `/journal`: decision journal entries
- `/journal/:journalId`: decision journal detail
- `/postmortems`: scheduled postmortem tasks
- `/reports`: Reports Center for safe local Markdown/JSON artifacts
- `/research` and `/research/:researchId`: read-only research context explorer
- `/macro` and `/macro/:macroId`: read-only macro context explorer
- `/senior-memos` and `/senior-memos/:memoId`: read-only senior memo explorer
- `/governance`: read-only governance/context health explorer
- `/system`: read-only system boundaries and packaging readiness

Unknown routes render a local 404 fallback with links back to the dashboard and system boundaries.

## Mock Mode

The normal mode uses live FastAPI responses. Network failures switch read queries to clearly labelled fake data. HTTP 4xx/5xx errors remain visible and do not trigger fallback.

All POST mutations are disabled in mock mode and never fake official success.

To force sample data, create `frontend/.env.local` with:

```text
VITE_USE_MOCKS=true
```

Mock records are labelled `[샘플]` or `DEMO-*`, and the shell displays the mock source and reconnect action.

## Safety Boundaries

- No broker integration
- No automatic trading
- No frontend SQLite access
- No frontend CLI subprocess
- Risk Engine remains official ticket authority
- Reconciliation remains the confirmation boundary
- Override is a declared exception, not official risk validation
- Research, macro, senior memo, governance, and reports are read-only context surfaces

## Checks

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```
