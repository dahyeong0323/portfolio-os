# Frontend Stage 1 API Contract

## Boundary

The API is a read-only adapter over the existing Portfolio OS services, repositories, dataclasses, state machine, and SQLite database.

```text
React -> FastAPI -> existing Portfolio OS domain layer -> SQLite
```

The API does not invoke the CLI, create subprocesses, initialize databases, run migrations, or expose mutation routes.

## Common Rules

- Base prefix: `/api/v1`
- Decimal values: JSON strings, preserving decimal precision
- Dates: `YYYY-MM-DD`
- Datetimes: ISO 8601, with UTC values emitted using `Z`
- Missing collections: empty arrays
- Missing latest reconciliation: HTTP 200 with `found=false`
- Missing or incomplete database: read endpoints return HTTP 503
- `/health` remains available with HTTP 200 and reports degraded readiness

Errors use this shape:

```json
{
  "error": {
    "code": "database_not_ready",
    "message": "The Portfolio OS database migrations are not ready.",
    "details": null
  }
}
```

## Routes

### `GET /api/v1/health`

Returns API status, application mode, database reachability, database readiness, and applied/expected migration counts and versions.

### `GET /api/v1/ledger/status`

Returns the current `LedgerStateMachine` status, latest successful reconciliation time, mutually exclusive status flags, and a short explanation.

### `GET /api/v1/ledger/snapshot`

Optional query parameter: `as_of_date`. The default is the server's current date.

Returns the existing `LedgerSnapshotBuilder` result: positions, cash, liabilities, tax reserves, generation time, and ledger status.

### `GET /api/v1/accounts`

Returns all accounts, including inactive accounts, with total, active, and inactive counts.

### `GET /api/v1/instruments`

Returns all instruments, including inactive instruments, with total, active, and inactive counts.

### `GET /api/v1/reconciliations/latest`

Returns `found` and the latest stored reconciliation. Stored JSON fields are decoded into typed position, cash, liability, tax reserve, and difference arrays. Raw SQLite rows and encoded JSON columns are not exposed.

Only the cash and quantity tolerances are included because those are the tolerance values persisted by the current reconciliation schema.

### `GET /api/v1/tickets`

Returns every existing Stage 2 order ticket and its persisted status. It does not calculate or authorize state transitions.

### `GET /api/v1/executions/pending`

Returns existing manual execution rows whose status is exactly `pending_reconciliation`, matching `ManualExecutionRepository.list_pending()`.

## OpenAPI

Swagger UI is available at `/docs`, ReDoc at `/redoc`, and the OpenAPI document at `/openapi.json` while the local server is running.
