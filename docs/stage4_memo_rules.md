# Stage 4 Memo Rules

## Valid Inputs

- Research packets must have `packet_status = 'valid'` and `qa_status = 'passed'`.
- Macro context packets must have `packet_status = 'valid'`.
- Empty research input is allowed only when `portfolio_only = 1`.

## Valid Memo QA

A valid memo requires all 10 required sections, at least one no-action alternative, one opposing argument, one decision change trigger, valid upstream inputs, and zero forbidden execution-authority language hits.

## Candidate Actions

Candidate action class is deterministic:

- `create_intent_candidate`: `risk_increasing`
- `reduce_risk_candidate`: `risk_reducing`
- `correction_review`: `correction`
- `no_action`, `review`, `watchlist_update`, `research_needed`: `review_only`

If ledger status is not `reconciled`, risk-increasing candidates are blocked pending reconciliation.

## Report Disclaimers

Every Senior Memo report states that it is not an order ticket, not a risk validation, and not execution authorization.
