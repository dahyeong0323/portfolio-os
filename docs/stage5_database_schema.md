# Stage 5 Database Schema

Stage 5 adds migrations `045` through `063` only. Stage 1 through Stage 4 migrations are unchanged.

## Tables

- `governance_policies`: policy registry, one active policy enforced by partial unique index.
- `governance_policy_rules`: active governance rules and thresholds.
- `configuration_snapshots`: active policy/template/schema configuration digest.
- `template_registry`: named templates.
- `template_versions`: versioned template body, SHA-256 hash, activation state.
- `golden_test_sets`: named canary/golden test sets.
- `golden_test_cases`: authority-boundary and context-boundary test cases.
- `canary_runs`: canary execution status and counts.
- `canary_results`: per-check result rows.
- `context_packages`: review/context packages with copied ledger status.
- `context_package_items`: allowed upstream context references.
- `context_budget_records`: item-count and deterministic token estimates.
- `delta_reviews`: package-to-package item deltas.
- `memory_items`: active/inactive operating memory.
- `system_health_snapshots`: green/yellow/red operational health snapshots.
- `read_only_integration_sources`: read-only source registry, constrained to `read_only_confirmed = 1`.
- `read_only_import_runs`: audit records for read-only imports.
- `governance_audit_events`: governance/canary warning and failure events.

## Allowed Context Item Types

- `reconciliation`
- `risk_validation`
- `order_ticket`
- `execution`
- `override`
- `research_packet`
- `macro_context`
- `senior_memo`
- `journal`
- `postmortem`
- `system_health`
- `memory`

## Protected Earlier Tables

Stage 5 tests assert that CLI flows do not change protected Stage 1 through Stage 4 row counts, including ledger, risk, ticket, execution, override, journal, research, macro, and Senior Memo tables.
