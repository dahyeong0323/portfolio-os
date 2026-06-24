# Frontend Stage 4 Handoff for Stage 5

## Completed stage

Frontend Stage 4 implemented the browser-accessible foundation for the Stage 2 risk-gated manual operating loop. Users can create a transaction intent, run the official backend Risk Engine, create an official manual order ticket from a passed or adjusted validation, and review the linked ticket detail.

## Stable outputs and interfaces

- `POST /api/v1/intents`
- `POST /api/v1/intents/{intent_id}/validate`
- `GET /api/v1/risk/validations/{risk_validation_id}`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- Frontend routes `/risk`, `/tickets`, and `/tickets/:ticketId`
- Typed frontend hooks `useCreateIntent`, `useValidateIntent`, `useRiskValidationById`, `useCreateTicketFromValidation`, and `useTicketById`

The ticket detail response includes typed ticket, linked intent summary, linked risk validation, parsed event payloads, and server-provided available/blocked actions.

## What Frontend Stage 5 may consume

- Persisted risk validation results and ticket ids returned by Stage 4.
- Ticket status and event timeline returned by the backend.
- Server-provided blocked actions explaining that approval, modification, rejection, and manual execution are deferred.
- Existing Mission Control layout, query/mutation client, status badges, tables, and mock-mode guardrails.

## What Frontend Stage 5 must not bypass

- Stage 1 ledger truth and `ledger_status`.
- Stage 2 Risk Engine validation.
- Official ticket creation from a passed or adjusted `RiskValidationResult`.
- Existing ticket service/state-machine rules.
- The rule that React must never read SQLite, call the CLI, parse CLI stdout, or call brokers directly.

## Preserved invariants

- No broker write, automatic trading, or execution path was introduced.
- Manual execution logs are not created by Stage 4.
- Reconciliation tables, override tables, manual execution tables, and historical transactions are not mutated by Stage 4 ticket creation/detail reads.
- Decimal values remain strings in API responses and frontend rendering.
- Mock mode cannot create fake official intents, validations, or tickets.

## Known limitations

- Approval, rejection, modification, and manual execution logging are intentionally deferred.
- There is no authentication or role-based authorization.
- Risk policy and price snapshot management remain CLI/domain concerns.
- Ticket event payloads are displayed structurally but no audit export UI exists.

## Verification status

As of June 16, 2026:

- `python -m pytest -q`: passed, 80 tests.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run lint`: passed.
- `npm.cmd run test`: passed, 6 files and 27 tests.
- `npm.cmd run build`: passed.
- `python -m compileall -q src tests`: passed.
- Source safety search passed for frontend direct SQLite access, CLI subprocess usage, and forbidden direct-trade CTA strings.
- OS-level `Invoke-WebRequest` confirmed HTTP 200 for `http://127.0.0.1:8000/api/v1/health`.
- OS-level `Invoke-WebRequest` confirmed HTTP 200 for `http://127.0.0.1:5173/risk`.

The in-app browser verification is inconclusive because the browser runtime could not maintain access to the temporary localhost servers. This does not contradict the OS-level HTTP checks, which returned 200.

`npm audit` was not completed because external registry metadata access was blocked by the approval policy.

Implementation details are recorded in `docs/frontend/stage4_implementation_report.md`, and the HTTP contract is `docs/frontend/stage4_operating_loop_api_contract.md`.
