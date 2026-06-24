# Frontend Stage 3 Reconciliation API Contract

## Scope

Frontend Stage 3 adds one external-snapshot import endpoint and three reconciliation endpoints. These endpoints do not approve tickets, confirm executions, call brokers, or create trading authority.

## Endpoints

### `POST /api/v1/snapshots/external-imports`

Accepts multipart form data:

- `account_id`: required positive integer
- `as_of_date`: required ISO date
- `positions_file`: optional UTF-8 CSV with `symbol,currency,quantity`
- `cash_file`: optional UTF-8 CSV with `currency,amount`
- `liabilities_file`: optional UTF-8 CSV with `liability_name,currency,current_amount`
- `tax_reserves_file`: optional UTF-8 CSV with `tax_year,tax_type,currency,reserved_amount`

At least one CSV is required. The default per-file limit is 5 MiB. The response contains an opaque UUID `artifact_id`, account, date, row counts, warnings, and import timestamp. Original filenames and server paths are not exposed.

### `POST /api/v1/reconciliations`

Accepts JSON:

```json
{
  "artifact_id": "opaque-uuid",
  "account_id": 1,
  "as_of_date": "2026-06-15"
}
```

The date is optional but, when provided, must match the artifact. The endpoint runs `LedgerSnapshotBuilder`, the existing `ReconciliationService`, repository persistence, ledger state transition, and existing report writer through `ReconciliationWorkflowService`.

The response contains the reconciliation id and status, resulting ledger status, over-tolerance difference counts, report availability, explanation, and warnings.

### `GET /api/v1/reconciliations/{reconciliation_id}`

Returns the typed stored reconciliation: expected and actual positions, cash, liabilities, tax reserves, all difference rows, tolerances, statuses, timestamps, and failure reason. Decimal values are JSON strings.

### `GET /api/v1/reconciliations/{reconciliation_id}/report`

Returns the generated Markdown report as JSON content with an opaque report reference. It never returns an absolute filesystem path.

## Authority and mutation boundary

- External snapshot values remain comparison actuals and are never inserted into `cash_balances`.
- A passed reconciliation confirms only previously unconfirmed transactions through the artifact date and marks eligible internal cash anchors reconciled.
- Failed or needs-review reconciliation does not confirm those records.
- Manual executions, tickets, overrides, and broker state are not mutated.
- Snapshot and report references are resolved under configured server directories and do not accept arbitrary paths.
- GET dashboard dependencies continue to use query-only SQLite connections. Only the two Stage 3 POST endpoints use the migration-checked writable dependency.

## Errors

Errors use the existing envelope:

```json
{
  "error": {
    "code": "invalid_snapshot_headers",
    "message": "The cash CSV is missing required headers.",
    "details": {"missing": ["amount"]}
  }
}
```

Expected error families include missing or oversized files, invalid encoding or headers, account/artifact/date mismatch, missing reconciliation/report, unavailable database, and incomplete migrations. Internal stack traces are not returned.

## Configuration

- `PORTFOLIO_OS_DB_PATH`: SQLite path
- `PORTFOLIO_OS_APP_MODE`: defaults to `local-reconciliation`
- `PORTFOLIO_OS_SNAPSHOT_DIR`: defaults to `data/imports/account_snapshots`
- `PORTFOLIO_OS_REPORT_DIR`: defaults to `data/exports/reconciliation_reports`
- `PORTFOLIO_OS_UPLOAD_LIMIT_BYTES`: defaults to 5 MiB
