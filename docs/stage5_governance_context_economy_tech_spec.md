# Portfolio OS Stage 5 Tech Spec

## Purpose

Stage 5 implements governance, context economy, canary/golden checks, system health, memory, delta review, and optional read-only integration audit records.

Stage 5 does not add trading authority. It cannot create order tickets, risk validations, approvals, manual executions, broker writes, or recommendations.

## Implemented Modules

- `portfolio_os.governance`: governance policies, rules, configuration snapshots, templates, golden tests, canaries, health snapshots, audit events, reports.
- `portfolio_os.context`: context packages, item validation, budget records, delta reviews, memory, reports.
- `portfolio_os.integrations`: read-only source registration and import audit records.
- `portfolio_os.cli.stage5_commands`: Stage 5 CLI registration.

## Upstream Contracts

Stage 5 may read Stage 1 through Stage 4 tables. It writes only Stage 5 tables and Stage 5 report files.

Valid context inputs are explicitly checked:

- `research_packet`: `packet_status='valid'` and `qa_status='passed'`
- `macro_context`: `packet_status='valid'`
- `senior_memo`: `memo_status='valid'` and `qa_status='passed'`

Order tickets are context only. Executions are history/context only.

## Default Governance Policy

`seed-default-governance-policy` creates `stage5_default_governance v1.0.0`.

Rules:

- `VALID_MEMO_ONLY`
- `VALID_RESEARCH_ONLY`
- `VALID_MACRO_ONLY`
- `NO_AUTHORITY_ESCALATION`
- `MAX_CONTEXT_ITEMS=50`
- `CONTEXT_BUDGET_WARNING_ITEMS=40`
- `CANARY_REQUIRED_BEFORE_TEMPLATE_ACTIVATION`
- `READ_ONLY_INTEGRATION_ONLY`

The default policy can be activated without a prior canary. Non-default or modified template activation requires the latest canary run to have `run_status='passed'`.

## Reports

Stage 5 writes Markdown and JSON reports under:

- `data/exports/governance_reports/`
- `data/exports/context_packages/`
- `data/exports/canary_reports/`
- `data/exports/health_reports/`

Each report states that it is not order authority.
