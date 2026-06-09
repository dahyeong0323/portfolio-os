# Stage 3 Macro Context Rules

Macro context is read-only context. It is not permission to buy, sell, size, approve, validate, or execute.

## Portfolio Context

`PortfolioContextBuilder` reads Stage 1/2 objects and writes only `portfolio_context_snapshots`. The snapshot is a cache for context, not ledger truth.

## Macro Metrics and Correlations

- Macro metrics are stored as decimal text.
- Correlation values must be between `-1` and `1`.
- Missing inputs are represented as `unknown`, not guessed.

## Macro Regime

The MVP classifier returns `normal`, `stress`, `crisis`, or `unknown` from recorded metrics and correlations. The classification is informational only.

## Macro Context Packet

Macro context packets can be `draft`, `valid`, `invalid`, or `archived`. Validation rejects summary text that contains recommendation or order-authority language.
