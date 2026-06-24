# Frontend Stage 1 Handoff for Frontend Stage 2

## Completed Stage

Frontend Stage 1 added a thin, read-only FastAPI layer over the implemented Portfolio OS Stage 1 through Stage 5 domain system.

It provides health, ledger status, ledger snapshot, account, instrument, latest reconciliation, order ticket, and pending manual execution reads. The API uses existing repositories, `LedgerSnapshotBuilder`, `LedgerStateMachine`, and the existing SQLite schema.

## Stable Outputs and Interfaces

- API prefix: `/api/v1`
- Eight GET routes documented in `frontend_api_contract.md`
- Pydantic-generated OpenAPI at `/openapi.json`
- Decimal values serialized as strings
- ISO date and datetime values
- Structured error envelope with `code`, `message`, and `details`
- Clean empty states for lists and latest reconciliation
- SQLite URI `mode=ro` and query-only request database connections

## What Frontend Stage 2 May Consume

- The eight read-only endpoints
- The generated OpenAPI schema for frontend types or API client definitions
- Ledger status flags and explanation for status displays
- Ledger snapshot collections for read-only dashboard views
- Account, instrument, reconciliation, ticket, and pending execution data for read-only panels

## What Frontend Stage 2 Must Not Bypass

- Do not read SQLite directly from React.
- Do not call or parse the `portfolio-os` CLI from React or an API subprocess.
- Do not infer ledger truth independently of `LedgerStateMachine` and `LedgerSnapshotBuilder`.
- Do not infer, create, approve, reject, modify, or execute Stage 2 tickets in the frontend.
- Do not treat research, macro context, Senior Memos, governance data, or dashboard presentation as order authority.

## Preserved Invariants

- Stage 1 ledger status remains the downstream readiness gate.
- Stage 2 Risk Engine and ticket workflow remain the only official risk and order authority.
- External snapshot values are not inserted into `cash_balances`.
- Historical transactions are not directly mutated.
- SQLite remains server-side and local.
- No automatic trading, broker write, or cloud synchronization was introduced.
- Existing CLI entrypoints remain available.

## Known Limitations

- The API has no authentication or CORS policy yet.
- List routes have no pagination or filters.
- The latest reconciliation response exposes the persisted cash and quantity tolerances; the current database schema does not persist liability and tax reserve tolerance values.
- Health checks readiness but does not initialize or repair a database.
- There are no write endpoints and no React frontend in this stage.

## Verification Status

- Full pytest suite: 68 passed
- New API and serialization tests: 12 passed
- Compileall: passed
- Uvicorn startup and live `/api/v1/health`: passed
- Database readiness during smoke test: 63 of 63 migrations
- Protected table non-mutation: passed
- SQLite query-only enforcement: passed
- OpenAPI route contract: passed

No generated financial report or real user data was created or committed by this stage.
