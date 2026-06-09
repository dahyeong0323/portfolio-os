# Portfolio OS Stage 3 Handoff for Stage 4

## 1. Executive Summary

Stage 3 implemented the Fact Research and Macro Context layer. It prepares sourced facts, anti-thesis coverage, missing-data flags, and read-only macro context for later human review. Stage 3 does not create recommendations, Senior Memos, order tickets, risk validations, approvals, executions, or broker actions.

## 2. What Stage 3 Implemented

- Asset thesis registry.
- Research source registry.
- Fact-only research packet workflow.
- Bull, bear, neutral, thesis-supporting, and thesis-challenging fact records.
- Missing data records.
- Strict research QA.
- Forbidden recommendation-language lint.
- Research Markdown and JSON reports.
- Read-only portfolio context snapshots from Stage 1/2 objects.
- Macro metrics, correlations, macro regimes, crash playbook references, and macro context packets.
- Macro Markdown and JSON reports.
- Stage 3 CLI commands for all implemented flows.

## 3. Stable Stage 3 Outputs

Stage 4 may treat these as stable Stage 3 outputs:

- `research_packets` where `packet_status = 'valid'` and `qa_status = 'passed'`.
- `research_qa_results` linked to valid packets.
- `research_facts`, `research_missing_data`, and `research_sources` linked to valid packets.
- `macro_context_packets` where `packet_status = 'valid'`.
- `portfolio_context_snapshots` as read-only context cache, not ledger truth.
- `macro_regime_snapshots`, `macro_metric_snapshots`, and `correlation_snapshots` as context inputs.
- Research reports under `data/exports/research_reports/`.
- Macro context reports under `data/exports/macro_reports/`.

## 4. Stage 4 Entry Contract

Stage 4 may consume only valid research packets and valid macro context packets. Draft, invalid, archived, or not-run packets are not approved inputs.

Stage 4 must preserve these upstream gates:

- Stage 1 `ledger_status` remains authoritative for ledger readiness.
- Stage 2 Risk Engine remains authoritative for risk validation.
- Stage 2 ticket workflow remains authoritative for official order tickets.
- Stage 2 manual execution workflow remains authoritative for execution logging.

## 5. Stage 4 Must Not Bypass

Stage 4 must not:

- bypass Stage 1 `ledger_status`
- treat `portfolio_context_snapshots` as ledger truth
- bypass Stage 2 Risk Engine checks
- create official tickets without Stage 2 validation
- approve or execute orders from Stage 3 context
- treat research or macro context as order authority
- write external snapshot values into `cash_balances`
- mutate historical transactions directly

## 6. Recommended Stage 4 Starting Point

Stage 4 should start by reading a valid research packet and a valid macro context packet, then producing a human-facing memo artifact that explicitly preserves Stage 1 and Stage 2 gates. Any later memo must remain downstream of ledger truth and risk validation rather than replacing them.
