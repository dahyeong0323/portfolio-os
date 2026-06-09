# Stage 5 Governance Rules

## Authority Boundary

Stage 5 artifacts are review, governance, and context artifacts only. They are not:

- order tickets
- risk validations
- ticket approvals
- execution authorization
- broker write instructions
- investment recommendations

## Default Rules

- `VALID_MEMO_ONLY`: context packages may consume only valid Senior Memos with passed QA.
- `VALID_RESEARCH_ONLY`: context packages may consume only valid research packets with passed QA.
- `VALID_MACRO_ONLY`: context packages may consume only valid macro context packets.
- `NO_AUTHORITY_ESCALATION`: canary checks detect forbidden order-authority language.
- `MAX_CONTEXT_ITEMS=50`: context packages fail above 50 items.
- `CONTEXT_BUDGET_WARNING_ITEMS=40`: context packages warn at 40 items.
- `CANARY_REQUIRED_BEFORE_TEMPLATE_ACTIVATION`: non-default or modified template activation requires a latest passed canary.
- `READ_ONLY_INTEGRATION_ONLY`: integration source registration requires `read_only_confirmed=1`.

## Canary Behavior

Canary runs evaluate active golden test cases. Forbidden authority-language cases compare observed behavior with expected status. A canary fails if any check mismatches its expected status.

If no active golden cases exist, the built-in authority boundary check passes and records the no-authority boundary.
