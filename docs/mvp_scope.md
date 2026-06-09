# MVP Scope

This MVP is Macro-Stage 1: Ledger Truth Foundation.

The goal is to answer one question with evidence:

```text
Does the OS ledger match the real account snapshot as of this date?
```

## In Scope

- Initialize a local SQLite database.
- Define the Stage 1 schema and migration history.
- Create account and instrument master records.
- Record transactions with Decimal-only money and quantity values.
- Record internal cash anchors.
- Record liabilities and tax reserves.
- Build ledger snapshots for a target date.
- Import external account snapshot CSV data into normalized JSON artifacts.
- Reconcile ledger expected values against external actual values.
- Persist reconciliation snapshots.
- Export reconciliation reports as Markdown and JSON.
- Expose the Stage 1 workflow through the `portfolio-os` CLI.
- Test pass, fail, broken, and recovery reconciliation paths.

## Out of Scope

- Investment recommendations.
- Senior investor memo generation.
- Research agents.
- Macro and correlation risk layers.
- Risk-gated order tickets.
- Broker API execution.
- Telegram or other messenger automation.
- RAG, model QA, or context economy.
- Real-time market data streaming.
- Complex UI.

## Current CLI Surface

The implemented CLI commands are:

- `init-db`
- `add-account`
- `add-instrument`
- `record-transaction`
- `record-cash-balance`
- `record-liability`
- `record-tax-reserve`
- `import-external-snapshot`
- `run-reconciliation`
- `ledger-status`
- `export-reconciliation-report`
