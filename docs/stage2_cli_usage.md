# Stage 2 CLI Usage

All commands support the global `--db` option.

Example:

```powershell
portfolio-os --db data/portfolio_os.sqlite3 seed-default-risk-policy --base-currency CHF
```

## Policy and Market Inputs

- `record-price`
- `record-fx-rate`
- `list-prices`
- `list-fx-rates`
- `seed-default-risk-policy`
- `create-risk-policy`
- `activate-risk-policy`
- `add-risk-rule`
- `list-risk-rules`
- `set-instrument-risk-profile`

## Intent and Validation

- `create-intent`
- `validate-intent`
- `show-risk-validation`

## Tickets

- `create-order-ticket`
- `show-order-ticket`
- `approve-ticket`
- `reject-ticket`
- `modify-ticket`
- `expire-tickets`
- `list-open-tickets`

## Execution and Reconciliation

- `log-manual-execution`
- `list-pending-executions`
- `confirm-executions-after-reconciliation`

## Overrides and Journal

- `declare-override`
- `confirm-override`
- `log-override-execution`
- `list-overrides`
- `record-postmortem`
- `list-journal`
