# Frontend Stage 6 Reconciliation Confirmation API Contract

## Scope

Frontend Stage 6 adds a controlled confirmation workflow for manual executions that are already logged and waiting for reconciliation. The endpoint confirms eligible pending manual executions only after matching passed reconciliation evidence exists.

This stage does not place orders, call brokers, create new transactions, import reconciliation evidence, modify tickets, execute overrides, or replace the reconciliation workflow.

## Endpoint

### `POST /api/v1/executions/confirm-after-reconciliation`

Confirms pending manual executions against passed reconciliation evidence through `ManualExecutionService.confirm_after_reconciliation`.

Request fields:

- optional `reconciliation_id`
- optional `account_id`
- optional `as_of_date`
- optional `execution_ids`

Scoping rules:

- If `reconciliation_id` is provided, that reconciliation row is used.
- If `reconciliation_id` is omitted and `account_id` is provided, the latest reconciliation for that account is used.
- If `execution_ids` are provided without a reconciliation id, the latest matching reconciliation is selected, subject to the same passed-evidence gate.
- A global unscoped confirmation request with neither `reconciliation_id`, `account_id`, nor `execution_ids` is rejected.

Required evidence:

- reconciliation status must be `passed`
- reconciliation account scope must match the execution account when the reconciliation is account-scoped
- execution date and linked transaction trade date must be on or before the reconciliation `as_of_date`

Eligibility for each execution:

- `execution_status` must be `pending_reconciliation`
- `override_ticket_id` must be absent; override confirmation is deferred
- `created_transaction_id` must exist
- linked transaction must exist
- linked transaction must have `is_confirmed=true`
- linked transaction account must match the execution account

Response fields:

- `confirmation_run_id`
- `reconciliation_id_used`
- `total_pending_checked`
- `confirmed_execution_ids`
- `still_pending_execution_ids`
- `failed_execution_ids`
- `skipped_executions`
- `explanation`

Structured errors use the existing envelope:

```json
{
  "error": {
    "code": "confirmation_blocked",
    "message": "Manual execution confirmation requires matching passed reconciliation evidence.",
    "details": "reconciliation must be passed, got failed"
  }
}
```

Common rejection cases return HTTP `409`:

- reconciliation missing
- reconciliation status is `failed` or `needs_review`
- reconciliation scope does not match the requested account/date
- request is globally unscoped

## Upgraded Read Responses

### `GET /api/v1/executions/pending`

Pending execution rows now include:

- linked ticket summary
- `created_transaction_id`
- `pending_reconciliation`
- `transaction_is_confirmed`
- `reconciliation_evidence`
- `confirmation_eligible`
- `confirmation_blocked_reason`
- server-provided `available_actions`
- server-provided `blocked_actions`

### `GET /api/v1/executions/{execution_id}`

Execution detail now includes the same confirmation readiness fields, plus the provisional transaction summary when available.

## Preserved Boundaries

- Confirmation does not create transactions.
- Confirmation does not mutate reconciliation evidence rows.
- Confirmation does not mutate historical transaction contents directly.
- Confirmation does not call brokers or implement automatic trading.
- Confirmation does not handle override executions in this stage.
- Decimal values continue to serialize as JSON strings.
