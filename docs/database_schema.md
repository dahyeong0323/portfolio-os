# Database Schema

The Stage 1 database is SQLite. The default DB path is:

```text
data/portfolio_os.sqlite3
```

## Connection Pragmas

Every connection applies:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

## Migration History

The implementation adds `schema_migrations`:

| Column | Purpose |
|---|---|
| `version` | migration number |
| `name` | migration file name suffix |
| `applied_at` | UTC application time |
| `checksum` | SHA-256 checksum of migration SQL |

## Core Tables

### `accounts`

Stores account master data. It enforces account type, 3-letter base currency, active flag, and unique account name per institution.

### `instruments`

Stores instrument master data. It enforces instrument type, 3-letter currency, active flag, and unique `symbol + exchange + currency`.

### `transactions`

Stores append-only transaction records. Buy/sell records require `instrument_id`, `quantity`, and `price`. Voided transactions require `void_reason`.

Decimal-like values are stored as text-preserving `DECIMAL_TEXT` columns so Python can round-trip them as `Decimal`.

### `cash_balances`

Stores OS internal cash anchors only. It enforces unique `account_id + as_of_date + currency`.

Important rule:

```text
source = external_snapshot is not allowed in cash_balances.
```

External cash belongs in normalized external snapshot artifacts, not in this table.

### `liabilities`

Stores liability records by date. The snapshot builder selects the latest active record per `account_id + liability_name + liability_type + currency`.

### `tax_reserves`

Stores protected tax reserve records by date. The snapshot builder selects the latest active record per `account_id + tax_year + tax_type + currency`.

### `reconciliation_snapshots`

Stores reconciliation results and serialized expected, actual, and diff payloads. It enforces:

- `passed` results must end as `reconciled`.
- `failed` results must end as `broken`.
- `needs_review` results must end as `provisional` or `broken`.
- passed results must have zero over-tolerance diff counts.

## Decimal Storage Policy

SQLite does not enforce fixed precision decimal storage. The implementation stores Decimal values as strings and parses them back into Python `Decimal`.
