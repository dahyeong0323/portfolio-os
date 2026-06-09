# Stage 4 Database Schema

Stage 4 adds migrations `036` through `044`. Stage 1, Stage 2, and Stage 3 migrations remain unchanged.

## Tables

- `senior_memo_input_bundles`: reproducible upstream input snapshot, including explicit `portfolio_only`.
- `senior_memos`: memo metadata, status, scope, executive summary, and QA state.
- `senior_memo_sections`: required structured memo sections.
- `decision_candidates`: non-authoritative candidate actions with `candidate_action_class`, status, next step, risk-validation flag, and reconciliation-first flag.
- `no_action_alternatives`: explicit no-action alternatives.
- `opposing_arguments`: strongest opposing arguments.
- `decision_change_triggers`: conditions that would change the memo judgment.
- `senior_memo_qa_results`: completeness and authority-boundary QA results.

## Protected Upstream Tables

Stage 4 must not write to ledger, reconciliation, Stage 2 operating, decision journal, Stage 3 research, or Stage 3 macro context tables.
