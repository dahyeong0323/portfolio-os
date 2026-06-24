# Portfolio OS Frontend References

Portfolio OS frontend implementation research and visual references are kept in this directory.

## Files

- `portfolio_os_frontend_deep_research_v2.md`: frontend architecture, product priorities, screen structure, and implementation recommendations.
- `assets/mission_control_dashboard_reference.png`: Mission Control-style dashboard visual reference used by the research document.
- `frontend_api_contract.md`: stable Frontend Stage 1 HTTP response and error contract.
- `stage1_api_usage.md`: local installation, configuration, and run commands.
- `stage1_implementation_report.md`: factual implementation and verification summary.
- `stage1_handoff_for_stage2.md`: constraints and stable inputs for the next frontend stage.
- `stage2_implementation_report.md`: factual Mission Control implementation and verification summary.
- `stage2_handoff_for_stage3.md`: stable frontend interfaces, preserved authority boundaries, and limitations for the next frontend stage.
- `stage3_reconciliation_api_contract.md`: snapshot upload, reconciliation run, detail, report, and error contracts.
- `stage3_implementation_report.md`: factual browser reconciliation implementation and verification summary.
- `stage3_handoff_for_stage4.md`: stable Frontend Stage 3 interfaces and preserved constraints for the next frontend stage.
- `stage4_operating_loop_api_contract.md`: intent, risk validation, ticket creation, and ticket detail API contract.
- `stage4_implementation_report.md`: factual Stage 4 operating loop implementation and verification summary.
- `stage4_handoff_for_stage5.md`: stable Stage 4 interfaces and preserved constraints for manual execution work.
- `stage5_manual_execution_api_contract.md`: ticket approval, rejection, manual execution logging, and pending execution API contract.
- `stage5_implementation_report.md`: factual Stage 5 human approval and manual execution implementation summary.
- `stage5_handoff_for_stage6.md`: stable Stage 5 interfaces and deferred Stage 6 boundaries.
- `stage6_reconciliation_confirmation_api_contract.md`: pending manual execution confirmation API contract.
- `stage6_implementation_report.md`: factual Stage 6 reconciliation confirmation implementation summary.
- `stage6_handoff_for_stage7.md`: stable Stage 6 interfaces and deferred Stage 7 boundaries.
- `stage7_override_journal_api_contract.md`: override, decision journal, and postmortem task API contract.
- `stage7_implementation_report.md`: factual Stage 7 override and audit-memory implementation summary.
- `stage7_handoff_for_stage8.md`: stable Stage 7 interfaces and deferred Stage 8 boundaries.

The runnable React application and its local commands are documented in `../../frontend/README.md`.

## Usage

- Treat the research document as implementation guidance, not as evidence that a feature already exists.
- Preserve Stage 1 ledger truth and the Stage 2 risk and ticket workflow as upstream gates in any frontend or API work.
- Use the image for visual direction only. Domain state, labels, counts, dates, and portfolio values shown in it are illustrative.
- Verify proposed interfaces against the current services, repositories, migrations, tests, and stage handoff documents before implementation.

## Provenance

The source files were supplied on June 14, 2026 and copied into the repository without modifying their contents.
