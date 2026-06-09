# Portfolio OS Stage 3: Fact Research and Macro Context

Stage 3 implements the fact research and macro context layer. It creates sourced research packets and read-only macro context packets. It does not recommend trades, create order tickets, approve orders, size positions, validate risk, or log executions.

## Runtime Contract

- Runtime dependencies: standard library only.
- Development dependency: pytest only.
- Database: SQLite through the existing migration runner.
- CLI: argparse through `portfolio-os`.
- Decimal policy: persisted numeric macro values use canonical decimal text.

## Implemented Components

- `src/portfolio_os/research/`: theses, sources, research packets, facts, missing data, QA, lint, reports.
- `src/portfolio_os/macro/`: portfolio context snapshots, macro metrics, correlations, regimes, crash playbook rules, macro context packets, reports.
- `src/portfolio_os/cli/stage3_commands.py`: Stage 3 CLI command registration.
- `migrations/023` through `035`: Stage 3 schema only.

## Non-Authority Rule

Research packets and macro context packets are context artifacts only. They cannot create, approve, size, validate, or execute trades.
