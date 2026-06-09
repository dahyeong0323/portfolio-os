# Reconciliation Rules

Reconciliation compares the OS ledger snapshot with an external account snapshot.

## Expected vs Actual

- Expected values come from `LedgerSnapshotBuilder`.
- Actual values come from normalized external snapshot JSON artifacts.
- External CSV values are not inserted into OS ledger tables before reconciliation.

## Default Tolerances

| Type | Tolerance |
|---|---:|
| cash | `1.00` |
| quantity | `0.000001` |
| liability | `1.00` |
| tax reserve | `1.00` |

Differences inside tolerance are retained in detail output but are not counted as reconciliation failures.

## Position Matching

External position import resolves instruments as follows:

1. If `instrument_id` is supplied, it must exist and match `symbol`, `currency`, and optional `exchange`.
2. If `instrument_id` is not supplied, the importer searches by `symbol + currency + exchange`.
3. Exactly one match is accepted.
4. Zero matches become `missing`.
5. Multiple matches become `ambiguous`.

Unresolved position matches produce `needs_review` and ledger status `broken`.

## Cash Comparison

OS cash expected values are calculated from:

```text
latest internal cash anchor per account/currency
+ transaction net_cash_amount after that anchor
```

If there is no internal cash anchor, transaction cash movement is used from zero.

External cash actual values come only from the external snapshot artifact.

## Liability Comparison

Liability comparison key:

```text
account_id + liability_name + currency
```

The ledger snapshot includes `liability_type` for clarity and internal scope selection.

## Tax Reserve Comparison

Tax reserve comparison key:

```text
account_id + tax_year + tax_type + currency
```

## Result Rules

- If all over-tolerance diff counts are zero and all instrument matches are resolved, result is `passed` and ledger status becomes `reconciled`.
- If any diff exceeds tolerance, result is `failed` and ledger status becomes `broken`.
- If required reference matching is missing or ambiguous, result is `needs_review` and ledger status becomes `broken`.

Reports are written as Markdown and JSON under:

```text
data/exports/reconciliation_reports/
```
