# Frontend Stage 4 Operating Loop API Contract

## Scope

Frontend Stage 4 exposes transaction intent creation, official Risk Engine validation, and official manual order ticket creation/review. It does not expose approval, rejection, modification, manual execution logging, broker writes, automatic execution, or frontend-side risk calculation.

## Endpoints

### `POST /api/v1/intents`

Creates a Stage 2 transaction intent through `TransactionIntentService`.

Request fields:

- `account_id`
- `instrument_id`
- `side`: `buy` or `sell`
- `currency`
- `requested_quantity` or `requested_notional`
- `limit_price`
- `rationale`
- optional `expires_at`

Response contains the typed intent and `next_available_actions`. Creating an intent is not a recommendation and does not create a ticket.

### `POST /api/v1/intents/{intent_id}/validate`

Builds a server-side ledger snapshot with `LedgerSnapshotBuilder`, runs `RiskEngine.validate_and_persist`, and updates intent status to `risk_passed`, `risk_adjusted`, or `risk_rejected`.

Request fields:

- optional `as_of_date`
- optional `policy_version_id`

Response contains the full structured validation, ledger status gate check, failed checks, warnings, explanation, and next actions. The frontend must not reproduce any risk calculation.

### `GET /api/v1/risk/validations/{risk_validation_id}`

Returns a persisted typed risk validation result from `RiskValidationRepository`.

### `POST /api/v1/tickets`

Creates an official manual order ticket through `OrderTicketService.create_ticket_from_validation`.

Request fields:

- `risk_validation_id`
- optional `expires_at`

Rejected and expired validations cannot create tickets. Passed and adjusted validations can create tickets. The response includes the ticket and server-provided available/blocked actions.

### `GET /api/v1/tickets/{ticket_id}`

Returns ticket detail, linked intent summary, linked risk validation, typed ticket event timeline, and available/blocked actions. Event payload JSON is parsed into `event_payload` objects before response serialization.

## Explicitly Not Exposed

Frontend Stage 4 does not add endpoints for:

- ticket approval
- ticket rejection
- ticket modification
- manual execution logging
- broker integration or broker write
- automatic trading
- frontend-side risk calculation

These actions may appear only as blocked or future actions in responses and UI copy.

## Preserved Authority Boundaries

- Existing GET endpoints remain query-only.
- New mutation endpoints use the scoped writable DB dependency.
- Stage 1 ledger status is read through the existing ledger builder/state machine.
- Stage 2 Risk Engine is the only risk authority.
- Tickets are created only from existing passed or adjusted persisted validations.
- Approval, rejection, modification, manual execution, override, broker, and reconciliation state are not mutated by ticket creation or detail reads.
- Decimal values remain JSON strings.

## Errors

Errors use the existing envelope:

```json
{
  "error": {
    "code": "risk_validation_rejected",
    "message": "Rejected risk validations cannot create order tickets.",
    "details": null
  }
}
```

Expected codes include `account_not_found`, `instrument_not_found`, `intent_not_found`, `invalid_as_of_date`, `risk_validation_failed`, `risk_validation_not_found`, `risk_validation_rejected`, `ticket_create_blocked`, and `ticket_not_found`.
