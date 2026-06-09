# Final Portfolio OS Operating Contract

## Final System Rule

Portfolio OS is ledger-first, risk-gated, macro-aware, human-approved, and governance-audited.

No component can create, approve, size, validate, or execute a trade unless it belongs to the explicit Stage 2 workflow.

## Stage Contracts

### Stage 1

The ledger is the source of truth. `ledger_status` is the readiness signal for downstream workflows.

### Stage 2

The Risk Engine, order ticket workflow, override flow, manual execution log, and decision journal are the only official operating loop for trade-related actions.

### Stage 3

Research packets and macro context are fact/context artifacts. They cannot recommend, approve, size, or execute trades.

### Stage 4

Senior Memos are human review artifacts. Decision candidates still require Stage 1 reconciliation and Stage 2 risk/ticket workflows where applicable.

### Stage 5

Governance, canaries, context packages, memory, system health, and read-only integration audits keep the system bounded and auditable. They do not add authority.

## Non-Negotiable Boundaries

- No automatic execution.
- No broker write integration.
- No order ticket creation outside Stage 2.
- No risk validation creation outside Stage 2.
- No Senior Memo as order authority.
- No context package as order authority.
- No invalid upstream artifact inside a valid context package.
- No read-write integration source in Stage 5.

## Roadmap Endpoint

There is no Stage 6 in the current roadmap. Stage 5 is the current final operating layer for governance and context economy.
