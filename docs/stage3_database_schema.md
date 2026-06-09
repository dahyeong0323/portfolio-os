# Stage 3 Database Schema

Stage 3 adds migrations `023` through `035`. Stage 1 and Stage 2 migrations remain unchanged.

## Research Tables

- `asset_theses`: current asset thesis text and watch questions.
- `research_sources`: cited source registry; each source requires `url` or `local_path`.
- `research_packets`: fact-only packet metadata and QA state.
- `research_facts`: sourced bull, bear, and neutral facts with thesis relation.
- `research_missing_data`: explicit unknowns and missing research questions.
- `research_qa_results`: strict QA counts, failure reasons, and warnings.

## Macro Tables

- `portfolio_context_snapshots`: read-only context cache from Stage 1/2.
- `macro_metric_snapshots`: manually recorded macro metrics.
- `correlation_snapshots`: manually recorded correlation or beta context.
- `macro_regime_snapshots`: deterministic context classification.
- `crash_playbook_rules`: reference-only crash playbook context rules.
- `macro_context_packets`: read-only portfolio macro context packets.

## Protected Tables

Stage 3 code must not write to `transactions`, `cash_balances`, `risk_validation_results`, `order_tickets`, `manual_execution_logs`, `override_tickets`, or `decision_journal`.
