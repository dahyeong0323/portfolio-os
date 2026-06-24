# Portfolio OS Demo Script

## 0. Setup

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

Open `http://127.0.0.1:5173`. The API runs at `http://127.0.0.1:8000`, and Vite proxies `/api` to FastAPI.

## 1. Opening

Portfolio OS is a local Mission Control system for personal portfolio operations, designed to separate ledger truth, risk validation, human approval, reconciliation evidence, and audit memory.

## 2. Dashboard

Open the dashboard at `/`. Show the Mission Control overview: ledger status, latest reconciliation state, open tickets, pending manual executions, overrides, postmortems, reports, and context health.

Explain that this is not a trading screen. It is an operating dashboard that shows which parts of the portfolio workflow need attention.

## 3. Reconciliation

Open `/reconciliation`. Show the external CSV snapshot import step, then the reconciliation workflow.

Walk through the idea: external broker/account snapshots become artifacts, Portfolio OS compares them against ledger truth, and the diff/report view shows whether the ledger and external evidence match.

## 4. Risk-Gated Manual Loop

Open `/risk`. Show the intent form, Risk Engine validation result, and order ticket creation path.

Explain that an intent is not an order. The Risk Engine is the official risk authority, and only passed or adjusted validations can create official manual order tickets.

## 5. Human Approval and Manual Execution

Open `/tickets`, then a ticket detail page. Show the approval/rejection controls and the manual execution logging area when the ticket is approved.

Explain that manual execution logging happens only after a human has executed externally in a broker app. Portfolio OS records that event; it does not place the broker order.

## 6. Reconciliation Confirmation

Open `/executions`. Show pending manual executions and the reconciliation confirmation path.

Explain that execution confirmation requires reconciliation evidence. A pending execution is not fully confirmed just because it was logged.

## 7. Override and Journal

Open `/overrides` and an override detail page. Show override declaration, linked journal entries, and postmortem task visibility.

Explain that an override is a declared exception. It is not official Risk Engine validation and does not become a hidden path to automatic execution.

## 8. Reports and Context

Open `/reports`. Show the Reports Center, category list, report detail, and plaintext report viewer.

Then open `/research`, `/macro`, `/senior-memos`, and `/governance`. Explain that these pages are read-only context surfaces. They support review and decision quality but do not create order authority.

## 9. Closing

Portfolio OS is not an automatic trading system. It is a local Mission Control system that makes authority boundaries explicit: ledger truth, Risk Engine, human approval, manual execution logging, reconciliation evidence, and audit memory each have separate roles.

The project demonstrates a disciplined investment workflow, a typed FastAPI/React architecture, and a safety-first approach to financial software design.
