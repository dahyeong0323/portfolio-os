# Stage 2 Risk Rules

The seeded default policy is a conservative local MVP policy, not investment advice.

`seed-default-risk-policy --base-currency <CODE>` creates `stage2_default_policy v1.0.0`.

Default rules:

| Rule | Value | Meaning |
|---|---:|---|
| `MIN_CASH_RESERVE` | `1000` | keep minimum cash in base currency |
| `DAILY_BUY_LIMIT` | `1000` | max daily buy capacity in base currency |
| `WEEKLY_BUY_LIMIT` | `3000` | max weekly buy capacity in base currency |
| `MAX_ORDER_NOTIONAL` | `1000` | max single order notional in base currency |
| `MAX_ASSET_WEIGHT` | `0.25` | max post-trade asset weight |
| `MAX_BUCKET_WEIGHT` | `0.50` | Stage 2 MVP bucket approximation limit |
| `TAX_RESERVE_PROTECTION` | `1.00` | tax reserves are fully protected |
| `DEBT_EXPOSURE_CHECK` | `0.50` | liabilities/gross portfolio value limit |

Buy intents are risk-increasing and require `ledger_status == reconciled`.

Sell intents are risk-reducing when holdings are sufficient. They may proceed with warnings on provisional or stale ledgers, but broken ledgers block official tickets.
