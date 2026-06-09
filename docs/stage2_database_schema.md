# Stage 2 Database Schema

Stage 2 extends Stage 1 with migrations `009` through `022`. Stage 1 migrations are not edited.

## New Tables

- `price_snapshots`: manual or CSV price references for valuation and risk checks.
- `fx_rates`: manual or CSV FX rates for cross-currency validation.
- `instrument_risk_profiles`: deterministic bucket and special-risk metadata per instrument.
- `risk_policy_versions`: versioned risk policy header with active policy and base currency.
- `risk_rules`: hard, adjustable, and warning thresholds for the active policy.
- `transaction_intents`: user trade intents before risk validation.
- `risk_validation_results`: immutable deterministic risk check results.
- `order_tickets`: human-readable, risk-validated manual order tickets.
- `order_ticket_events`: append-only ticket state transition log.
- `manual_execution_logs`: human-entered execution facts linked to either a ticket or override.
- `override_tickets`: declared exceptions when official ticket flow is blocked or bypassed.
- `decision_journal`: append-only human decision record.
- `postmortem_tasks`: scheduled reviews for important decisions or overrides.

## Important Constraints

- `manual_execution_logs` must link to exactly one of `order_ticket_id` or `override_ticket_id`.
- `order_tickets` require expiry.
- rejected validations cannot produce tickets at service level.
- execution service requires approved ticket or human-confirmed override.
- all Decimal values use `DECIMAL_TEXT` string storage.
