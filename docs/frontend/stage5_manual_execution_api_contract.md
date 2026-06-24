# Frontend Stage 5 Manual Execution API Contract

## Scope

Frontend Stage 5 exposes human approval, human rejection, and manual execution logging for official risk-validated order tickets. It does not expose ticket modification, reconciliation confirmation, override execution, broker writes, automatic trading, or frontend-side risk calculation.

## Endpoints

### `POST /api/v1/tickets/{ticket_id}/approve`

Approves a `validated` ticket through `OrderTicketService.approve_ticket`.

Request:

- optional `approval_note`
- optional `emotional_state`

Response includes the updated ticket, event timeline, linked decision journal entry id when available, `available_actions`, and `blocked_actions`.

Approval does not create a manual execution and does not place an order.

### `POST /api/v1/tickets/{ticket_id}/reject`

Rejects a `validated` ticket through `OrderTicketService.reject_ticket`.

Request:

- required `rejection_reason`
- optional `emotional_state`

Response includes the updated ticket, event timeline, linked decision journal entry id when available, `available_actions`, and `blocked_actions`.

Rejection preserves the audit trail and does not execute anything.

### `POST /api/v1/executions`

Logs a human manual execution after the user has already acted in an external broker app.

Request:

- `ticket_id`
- `filled_quantity`
- `fill_price`
- `fee`
- `tax`
- `executed_at`
- optional `broker_reference`
- optional `notes`

The endpoint uses `ManualExecutionService.log_execution_for_ticket`. Only approved tickets can be logged. The service creates a provisional Stage 1 transaction with `is_confirmed=false` and returns `pending_reconciliation=true`.

### `GET /api/v1/executions/{execution_id}`

Returns a typed manual execution detail, linked ticket when available, provisional transaction summary when available, and server-provided actions.

### `GET /api/v1/executions/pending`

Returns pending manual executions with linked ticket summaries, created provisional transaction ids, pending reconciliation flags, and blocked actions explaining that broker write and reconciliation confirmation are unavailable in this stage.

## Explicitly Not Exposed

- `POST /api/v1/tickets/{ticket_id}/modify`
- `POST /api/v1/executions/confirm-after-reconciliation`
- override execution endpoints
- broker integration or broker write endpoints
- automatic trading endpoints

## Preserved Boundaries

- React never reads SQLite, calls the CLI, parses CLI stdout, or calls brokers.
- Ticket state transitions are decided by existing backend services.
- Manual execution logging requires an approved ticket.
- Manual execution creates only a provisional transaction and waits for reconciliation.
- Decimal values remain JSON strings.
- Structured errors use the existing `{ "error": { "code", "message", "details" } }` envelope.
