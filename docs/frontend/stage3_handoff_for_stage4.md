# Frontend Stage 3 Handoff for Stage 4

## Completed stage

Frontend Stage 3 implemented a controlled browser reconciliation workflow over the existing Portfolio OS ledger and reconciliation domain. Users can import external snapshot CSVs, inspect the normalized artifact summary, run reconciliation, review typed differences, and read the generated Markdown report.

## Stable outputs and interfaces

- Existing GET routes from Frontend Stage 1 remain available.
- `POST /api/v1/snapshots/external-imports` imports an external actuals artifact and returns an opaque UUID.
- `POST /api/v1/reconciliations` runs the shared reconciliation workflow for that artifact.
- `GET /api/v1/reconciliations/{id}` returns the full typed persisted result.
- `GET /api/v1/reconciliations/{id}/report` returns generated Markdown without exposing server paths.
- `ReconciliationWorkflowService` is the shared CLI/API orchestration boundary.
- The frontend reconciliation route, mutation hooks, typed difference viewer, and report viewer are reusable Stage 4 UI inputs.

Decimal values remain strings in HTTP responses and frontend formatting. Artifact identifiers and report references are opaque, and raw SQLite rows are not exposed.

## What Frontend Stage 4 may consume

- Reconciliation status, resulting ledger status, typed differences, warnings, and report content.
- The existing Mission Control shell, runtime live/mock source indicator, TanStack Query provider, status badges, tables, and responsive tokens.
- The account list for account selection and the reconciliation detail id returned after a successful run.
- The established structured API error envelope.

## What Frontend Stage 4 must not bypass

- Stage 1 ledger truth must continue to come from `LedgerSnapshotBuilder` and `LedgerStateMachine`.
- External snapshot values must remain actual comparison inputs and must never be inserted into `cash_balances`.
- Historical transactions must not be directly edited; confirmation is allowed only through the passed reconciliation workflow and only through its date boundary.
- Stage 2 Risk Engine authority must remain upstream of ticket approval and execution.
- Research, Macro, Senior Memo, and Governance context must not become order authority.
- React must not access SQLite, invoke the CLI, parse CLI output, accept arbitrary server paths, or call brokers.

## Preserved invariants

- Failed and needs-review results do not confirm protected ledger records.
- Passed reconciliation does not confirm future-dated transactions.
- Ticket, execution, and override rows are unchanged by reconciliation.
- GET endpoints use query-only database connections; writable access is scoped to the import and run endpoints.
- Mock mode cannot perform or fake reconciliation mutations.
- No real financial data, database file, environment file, snapshot, export, or execution record is committed.

## Known limitations

- There is no authentication or user authorization around the two mutation endpoints.
- Imports and reports are local server artifacts without retention, listing, or deletion management.
- The workflow is synchronous and local; there are no background jobs, progress events, or automatic retry.
- The UI accepts CSV only and has no mapping preview before import.
- No trading, approval, execution, broker-write, or automatic action exists.

## Verification status

As of June 15, 2026:

- Complete Python suite: 74 passed with one upstream Starlette multipart deprecation warning.
- Frontend typecheck and ESLint: passed.
- Frontend Vitest: 5 files and 20 tests passed.
- Frontend production build: passed with Vite 8.0.16 and 1,654 modules transformed.
- Python module compilation: passed.
- npm dependency audit: 0 vulnerabilities.
- Source safety search and `git diff --check`: passed; Git reported line-ending notices only.
- In-app browser: the live five-step screen loaded against FastAPI with no console warnings or errors. The browser runtime did not expose local file selection automation or apply its requested viewport override, so multipart behavior and responsive breakpoints are covered by integration tests and CSS inspection rather than a complete browser-driven upload run.

Implementation details are recorded in `docs/frontend/stage3_implementation_report.md`, and the HTTP contract is `docs/frontend/stage3_reconciliation_api_contract.md`.
