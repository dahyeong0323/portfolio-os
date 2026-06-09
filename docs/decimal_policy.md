# Decimal Policy

Stage 1 treats Decimal correctness as a non-negotiable accounting rule.

## Values Covered

The following values must use Python `Decimal`:

- money
- quantity
- price
- fee
- tax
- FX rate
- liability amount
- tax reserve amount

## Accepted Input Shapes

Validation accepts:

- `Decimal("123.45")`
- numeric strings such as `"123.45"`
- integers such as `123`

Validation rejects:

- floats such as `123.45`
- booleans
- invalid decimal strings

## SQLite Storage

SQLite does not enforce exact fixed decimal semantics. The implementation stores Decimal values as text and reads them back into Python `Decimal`.

The migrations use `DECIMAL_TEXT` columns with `typeof(...) = 'text'` checks for Decimal-like fields.

## CLI Input

CLI arguments arrive as strings and are converted directly to `Decimal`. This keeps CLI money input out of binary floating point.

## Rationale

Portfolio OS Stage 1 is a money ledger. Allowing float values would make reconciliation and historical accounting vulnerable to silent precision drift.
