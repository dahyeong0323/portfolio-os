# Frontend Stage 7 Handoff for Stage 8

## Completed Stage

Frontend Stage 7 implemented explicit override declaration and the audit memory layer around overrides, decision journal entries, and scheduled postmortem tasks.

This stage is separate from the official Stage 4 Risk Engine flow. It records exceptions and human decisions; it does not validate orders, execute orders, or call brokers.

## Stable Outputs and Interfaces

- `GET /api/v1/overrides`
- `POST /api/v1/overrides`
- `GET /api/v1/overrides/{override_id}`
- `POST /api/v1/overrides/{override_id}/confirm`
- `POST /api/v1/overrides/{override_id}/cancel`
- `GET /api/v1/journal`
- `GET /api/v1/journal/{journal_id}`
- `GET /api/v1/postmortems`
- Frontend `/overrides`
- Frontend `/overrides/:overrideId`
- Frontend `/journal`
- Frontend `/journal/:journalId`
- Frontend `/postmortems`
- Server action strings:
  - `confirm_override`
  - `cancel_override`
  - `review_task`
- Deferred action strings:
  - `override_execution_deferred`
  - `record_completion_deferred`
  - `audit_export_deferred`
  - `broker_write_not_available`
  - `automatic_execution_not_available`

## What Stage 8 May Consume

- Override list and detail responses, including account and instrument summaries when available.
- Linked journal entries returned by override detail.
- Scheduled postmortem tasks linked to overrides.
- Journal filters by ticket, override, execution, risk validation, and decision type.
- Postmortem filters by status, linked override, and linked ticket.
- Existing dashboard alert and timeline integration points for overrides and postmortems.

## What Stage 8 Must Not Bypass

- Stage 1 ledger truth and ledger status.
- Stage 2 Risk Engine authority for official order-ticket flow.
- Stage 3 reconciliation evidence.
- Stage 4 intent to risk validation to official ticket creation boundaries.
- Stage 5 human approval before manual execution logging.
- Stage 6 passed reconciliation evidence before confirming pending manual executions.
- The rule that Portfolio OS does not place broker orders.
- The rule that override declaration is not official Risk Engine validation.

## Preserved Invariants

- React never reads SQLite directly.
- React never calls the CLI or parses CLI stdout.
- Decimal values remain strings at the API boundary.
- Raw SQLite rows are not exposed.
- Structured API errors keep the existing envelope.
- Override declaration creates no official order ticket.
- Override confirm and cancel create no execution record.
- No broker write path or automatic trading capability exists.
- Postmortem completion recording is not exposed.

## Known Limitations

- Override execution logging remains deferred.
- Postmortem completion recording remains deferred.
- There is no authentication, authorization, or role-based approval.
- There is no persistent audit export.
- There is no pagination UI, although backend journal and postmortem list helpers accept limit and offset.
- The frontend keeps mutation controls disabled in mock mode and never fakes override mutation success.

## Verification Status

As of June 19, 2026:

- `python -m pytest -q`: passed, 97 tests.
- `python -m compileall -q src tests`: passed.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run lint`: passed.
- `npm.cmd run test`: passed, 8 files and 36 tests.
- `npm.cmd run build`: passed.
- Source safety search on `frontend/src`: passed.
- OS-level backend health and frontend `/overrides`, `/journal`, and `/postmortems` checks returned HTTP 200.

Implementation details are recorded in `docs/frontend/stage7_implementation_report.md`, and the HTTP contract is `docs/frontend/stage7_override_journal_api_contract.md`.
