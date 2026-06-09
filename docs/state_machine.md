# Ledger State Machine

Stage 1 uses four ledger statuses:

```text
reconciled
provisional
stale
broken
```

## Status Meaning

| Status | Meaning |
|---|---|
| `reconciled` | Latest relevant ledger state has passed reconciliation against an external snapshot. |
| `provisional` | Ledger has no reconciliation yet, or new unconfirmed/unreconciled input exists. |
| `stale` | Last reconciliation is older than the configured freshness window. |
| `broken` | Reconciliation found unresolved or over-tolerance differences. |

## Implemented Rules

- No reconciliation history means `provisional`.
- A passed reconciliation can produce `reconciled`.
- A failed reconciliation produces `broken`.
- A `needs_review` reconciliation with unresolved differences produces `broken`.
- Unconfirmed transactions make the ledger `provisional`.
- Unreconciled cash anchors make the ledger `provisional`.
- While broken, a reversal or correction input can move the ledger back to `provisional`.
- A broken ledger does not become stale merely because time passes.
- The stale threshold is 7 days.

## Reconciled Guard

The database and state machine preserve the Stage 1 rule:

```text
No reconciled status without successful reconciliation snapshot.
```

In normal CLI flow, `run-reconciliation` persists the result. If it passes, related unconfirmed transactions and unreconciled internal cash anchors are marked reconciled/confirmed.
