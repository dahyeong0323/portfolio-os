# Frontend Stage 2 Handoff for Stage 3

## Completed stage

Frontend Stage 2 implemented the first read-only Mission Control shell. The React application consumes the Frontend Stage 1 FastAPI adapter and presents Dashboard, Ledger, Reconciliation, and Tickets pages without adding domain or database behavior.

## Stable outputs and interfaces

- Frontend root: `frontend/`
- Application routes: `/`, `/ledger`, `/reconciliation`, `/tickets`
- Backend contract: the eight existing `/api/v1` GET routes documented in `frontend_api_contract.md`
- API client: `frontend/src/api/client.ts`
- Manually fixed response types: `frontend/src/api/types.ts`
- Query hooks: `frontend/src/api/queries/`
- Explicit fake fallback: `frontend/src/api/mocks/`
- Semantic status mapping: `frontend/src/lib/statusMap.ts`
- Theme tokens and responsive layout: `frontend/src/styles/`

Decimal values remain strings from API response through rendering. The Vite development server proxies `/api` to `http://127.0.0.1:8000`, so backend CORS changes are not required for local development.

## What Frontend Stage 3 may consume

- Existing route shell, query provider, status badges, authority cards, tables, and empty/loading/error patterns.
- The runtime source store for live/mock indication and reconnect behavior.
- The existing read-only API responses and OpenAPI document.
- The responsive sidebar and Mission Control layout tokens.

## What Frontend Stage 3 must not bypass

- React must not read SQLite or invoke `portfolio-os` through subprocess.
- Stage 1 ledger status and reconciliation remain the source of ledger truth.
- Stage 2 Risk Engine authority must remain upstream of ticket approval or execution work.
- Senior Memo, Research, Macro, and Governance context must not be treated as order authority.
- External snapshot values must not be inserted into `cash_balances`.
- Historical transactions must not be directly mutated.
- No broker write, automatic trading, or unguarded execution path may be introduced.

## Preserved invariants

- The frontend issues only GET requests.
- No Stage 1 through Stage 5 domain logic or migration was changed by Frontend Stage 2.
- No real financial data, database, environment file, broker snapshot, import/export, or execution record is included in frontend assets.
- Mock records are labelled `[샘플]` or `DEMO-*` and the UI continuously identifies mock mode.
- Structured FastAPI 4xx/5xx responses are displayed as errors rather than hidden behind mock data.

## Known limitations

- Authentication, CORS policy, pagination, React production hosting, and write APIs are intentionally absent.
- Reconciliation import/run, intent creation, manual execution recording, and override declaration remain disabled placeholders.
- Ticket review is navigation to a read-only page only; approve, reject, modify, and execute actions do not exist.
- Market price, valuation, performance, and portfolio-weight data are unavailable and are not inferred.

## Verification status

As of June 14, 2026:

- Frontend typecheck, ESLint, Vitest, and production build pass.
- Vitest reports 4 files and 9 tests passed.
- The complete npm dependency audit reports 0 vulnerabilities.
- The complete Python suite reports 68 tests passed.
- Live FastAPI, backend-off mock fallback, reconnect, 1440x900 desktop, and 375x812 mobile behavior were verified in the in-app browser.
- The implementation report is `docs/frontend/stage2_implementation_report.md`.
