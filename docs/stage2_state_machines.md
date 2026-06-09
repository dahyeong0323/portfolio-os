# Stage 2 State Machines

## Transaction Intent

```text
drafted -> submitted -> risk_passed/risk_adjusted/risk_rejected -> ticket_created
```

Modified or cancelled intents are terminal for that intent.

## Risk Validation

Risk validations are immutable after creation.

```text
passed
adjusted
rejected
```

Only `passed` and `adjusted` validations can create order tickets.

## Order Ticket

```text
validated -> approved -> executed_provisional -> reconciled
validated -> rejected
validated -> modified
validated/approved -> expired
executed_provisional -> broken
```

No ticket can be executed unless it is approved.

## Manual Execution

```text
logged -> transaction_created -> pending_reconciliation -> reconciled
pending_reconciliation -> reconciliation_failed
```

Manual execution creates a Stage 1 transaction with `is_confirmed = 0`.

## Override

```text
risk_warned -> human_confirmed -> executed_provisional -> reconciled
risk_warned -> cancelled
```

Overrides require a human reason and are not official risk-validated tickets.
