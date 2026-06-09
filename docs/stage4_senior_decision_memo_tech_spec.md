# Portfolio OS Stage 4: Senior Decision Memo Layer

Stage 4 implements human-facing Senior Decision Memos. It reads Stage 1 ledger state, Stage 2 risk/ticket/execution context, and valid Stage 3 research/macro context. It does not create orders, risk validations, approvals, executions, or broker actions.

## Runtime Contract

- Runtime dependencies: standard library only.
- Development dependency: pytest only.
- Database: SQLite through the existing migration runner.
- CLI: argparse through `portfolio-os`.
- Stage 4 writes only Stage 4 tables and Senior Memo reports.

## Implemented Components

- `src/portfolio_os/senior/`: input bundles, memo records, sections, candidates, no-action alternatives, opposing arguments, change triggers, QA, lint, reports.
- `src/portfolio_os/cli/stage4_commands.py`: Stage 4 CLI command registration.
- `migrations/036` through `044`: Stage 4 schema only.

## Non-Authority Rule

Senior Memo output is a review artifact only. Any candidate action must go through the Stage 2 Risk Engine and ticket workflow.
