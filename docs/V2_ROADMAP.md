# V2 Roadmap

## v1.5 Completed Scope

Portfolio OS v1.5 Mission Control MVP is complete and tagged as `v1.5-mission-control-mvp`.

Completed scope includes:

- Local FastAPI `/api/v1` adapter
- SQLite ledger and audit database
- Ledger/account state dashboard
- External CSV reconciliation workflow
- Intent -> Risk Engine -> Order Ticket workflow
- Human approval and rejection
- Manual execution logging after external broker execution
- Reconciliation confirmation for pending manual executions
- Override declaration and decision journal visibility
- Scheduled postmortem task visibility
- Reports Center with safe plaintext rendering
- Research / Macro / Senior Memo / Governance read-only explorers
- System Boundaries page
- Final QA document and release tag

Final QA status:

- Backend: 105 passed, 1 warning
- Frontend: 46 passed
- Production build: PASS
- Safety search: PASS

## v2 Possible Scope

v2 should remain non-invasive and preserve the authority model established in v1.5. The default roadmap should improve usability, auditability, packaging, and review workflows without introducing automatic trading.

## Authentication / RBAC

Possible v2 work:

- Local user authentication for protected access.
- Role-based permissions for view-only, reviewer, and operator roles.
- Clear separation between read-only review and workflow mutation rights.
- Session handling and secure local configuration.

This should be designed before any hosted or shared deployment.

## Persistent Audit Export

Possible v2 work:

- Exportable audit bundles for tickets, executions, overrides, journal entries, postmortems, and reports.
- Stable export formats such as Markdown, JSON, CSV, or PDF.
- User-visible export history.
- Checks that exports do not include secrets or local-only private files by accident.

## Desktop Packaging

Possible v2 work:

- Desktop packaging after a permission model is defined.
- Local app shell that talks only to a configured local FastAPI endpoint.
- No shell plugin by default.
- No arbitrary filesystem access by default.
- No broker credentials in the frontend or desktop layer.

Tauri or another desktop packaging option should only be added after explicit security review.

## Broker Read-only Import

Possible v2 work:

- Broker/account import should start as read-only data ingestion.
- Imported data should become reconciliation evidence, not ledger truth by default.
- Imports should preserve the existing external snapshot and reconciliation boundaries.
- Import runs should be auditable and reversible where possible.

Broker write and automatic trading are not part of the default roadmap.

## Better Demo Dataset

Possible v2 work:

- Synthetic portfolio dataset for demos.
- Example accounts, instruments, transactions, reconciliation snapshots, tickets, executions, overrides, reports, and context records.
- Clearly labelled demo data so it cannot be mistaken for real portfolio data.
- Repeatable seed/reset command for local demos.

## Optional Deployment

Possible v2 work:

- Deployment only after authentication, RBAC, secret handling, audit export, and data privacy are designed.
- Read-only demo deployment may be considered before any operator workflow deployment.
- Hosted use should not expose real portfolio data without a dedicated security review.

## Explicit Non-goals

Broker write and automatic trading are not part of the default v2 roadmap.

Portfolio OS should continue to treat order placement as an external human action unless a future design explicitly changes the authority model and passes a separate security review.
