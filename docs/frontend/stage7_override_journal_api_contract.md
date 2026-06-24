# Frontend Stage 7 Override, Journal, and Postmortem API Contract

Frontend Stage 7 adds explicit override declaration and audit-memory read surfaces. It is not the official Risk Engine order path and it does not place broker orders.

All responses continue to use the existing JSON serialization rules:

- Decimal values are JSON strings.
- Dates and datetimes are ISO 8601 strings.
- Structured errors use `{ "error": { "code", "message", "details" } }`.
- Raw SQLite rows and stack traces are not exposed.

## Overrides

### `GET /api/v1/overrides`

Returns all override tickets.

Response:

```json
{
  "count": 1,
  "open_count": 1,
  "overrides": [
    {
      "override_id": 1,
      "status": "risk_warned",
      "override_type": "panic",
      "account_id": 1,
      "account_name": "Example Account",
      "instrument_id": 1,
      "instrument_symbol": "EXAMPLE",
      "instrument_name": "Example Instrument",
      "side": "sell",
      "requested_quantity": "1.000000",
      "requested_notional": null,
      "currency": "USD",
      "human_reason": "Explicit human reason",
      "human_final_choice": null,
      "risk_warning": "Risk warning text",
      "ledger_status_at_declaration": "reconciled",
      "mandatory_reconciliation_deadline": "2026-06-20",
      "mandatory_postmortem_date": "2026-06-26",
      "created_at": "2026-06-19T00:00:00Z",
      "updated_at": "2026-06-19T00:00:00Z",
      "linked_postmortem_task_id": 1,
      "available_actions": ["confirm_override", "cancel_override"],
      "blocked_actions": ["override_execution_deferred", "broker_write_not_available", "automatic_execution_not_available"]
    }
  ]
}
```

### `POST /api/v1/overrides`

Declares an explicit exception through `OverrideService.declare_override`.

Request:

```json
{
  "override_type": "panic",
  "account_id": 1,
  "instrument_id": 1,
  "side": "sell",
  "requested_quantity": "1.000000",
  "requested_notional": null,
  "currency": "USD",
  "human_reason": "Explicit human reason",
  "emotional_state": "calm"
}
```

Behavior:

- `human_reason` is required and must not be blank.
- `requested_quantity` and `requested_notional`, when provided, must not be negative.
- `account_id` must reference an existing account.
- `instrument_id`, when provided, must reference an existing instrument.
- The API records the override through the existing override service.
- The API schedules one postmortem task using `PostmortemTaskRepository.schedule` when the override has a mandatory postmortem date and no task exists yet.
- The API creates no official order ticket and no manual execution.

Response: `201`, same envelope as override detail.

### `GET /api/v1/overrides/{override_id}`

Returns one override with linked journal entries and the linked postmortem task when present.

Response:

```json
{
  "override": {
    "override_id": 1,
    "status": "risk_warned",
    "override_type": "panic",
    "account_id": 1,
    "account_name": "Example Account",
    "instrument_id": 1,
    "instrument_symbol": "EXAMPLE",
    "instrument_name": "Example Instrument",
    "side": "sell",
    "requested_quantity": "1.000000",
    "requested_notional": null,
    "currency": "USD",
    "human_reason": "Explicit human reason",
    "human_final_choice": null,
    "risk_warning": "Risk warning text",
    "ledger_status_at_declaration": "reconciled",
    "mandatory_reconciliation_deadline": "2026-06-20",
    "mandatory_postmortem_date": "2026-06-26",
    "created_at": "2026-06-19T00:00:00Z",
    "updated_at": "2026-06-19T00:00:00Z",
    "linked_postmortem_task_id": 1,
    "available_actions": ["confirm_override", "cancel_override"],
    "blocked_actions": ["override_execution_deferred", "broker_write_not_available", "automatic_execution_not_available"]
  },
  "linked_journal_entries": [],
  "postmortem_task": null,
  "explanation": "Override detail is an audit record, not a recommendation."
}
```

### `POST /api/v1/overrides/{override_id}/confirm`

Confirms an override decision through `OverrideService.confirm_override(..., final_choice="execute")`.

Request:

```json
{ "emotional_state": "calm" }
```

Behavior:

- Allowed only for `declared` or `risk_warned` overrides.
- Returns `409` for non-actionable states.
- Confirmation is an audit decision only. It is not broker execution and creates no manual execution record.

### `POST /api/v1/overrides/{override_id}/cancel`

Cancels an override decision through `OverrideService.confirm_override(..., final_choice="cancel")`.

Request:

```json
{ "emotional_state": "calm" }
```

Behavior:

- Blocked for `cancelled`, `executed_provisional`, `reconciled`, and `postmortem_completed`.
- Returns `409` for blocked states.
- Cancellation creates no order ticket, execution, broker write, or transaction.

## Journal

### `GET /api/v1/journal`

Returns decision journal entries with optional filters:

- `decision_type`
- `linked_ticket_id`
- `linked_override_id`
- `linked_execution_id`
- `risk_validation_id`
- `limit`
- `offset`

Response:

```json
{
  "count": 1,
  "entries": [
    {
      "decision_id": 1,
      "decision_type": "override_declared",
      "order_ticket_id": null,
      "override_ticket_id": 1,
      "risk_validation_id": null,
      "manual_execution_id": null,
      "human_decision": "declared",
      "reason": "Explicit human reason",
      "emotional_state": "calm",
      "context": {},
      "created_at": "2026-06-19T00:00:00Z"
    }
  ]
}
```

### `GET /api/v1/journal/{journal_id}`

Returns one decision journal entry. `context_json` is parsed and returned as a typed JSON object.

## Postmortems

### `GET /api/v1/postmortems`

Returns scheduled postmortem tasks with optional filters:

- `status`
- `linked_override_id`
- `linked_ticket_id`
- `limit`
- `offset`

Response:

```json
{
  "count": 1,
  "tasks": [
    {
      "postmortem_task_id": 1,
      "order_ticket_id": null,
      "override_ticket_id": 1,
      "due_date": "2026-06-26",
      "status": "scheduled",
      "prompt_questions": ["What was expected?", "What happened?", "What should change next time?"],
      "completed_decision_id": null,
      "created_at": "2026-06-19T00:00:00Z",
      "updated_at": "2026-06-19T00:00:00Z",
      "available_actions": ["review_task"],
      "blocked_actions": ["record_completion_deferred", "audit_export_deferred"]
    }
  ]
}
```

Postmortem completion recording is intentionally not exposed in Stage 7.

## Deferred

- Override execution logging.
- Postmortem completion recording.
- Ticket modification.
- Broker integration.
- Automatic trading.
- Authentication, RBAC, or persistent audit export.
