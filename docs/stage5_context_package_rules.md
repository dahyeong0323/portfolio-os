# Stage 5 Context Package Rules

## Purpose

Context packages assemble approved upstream artifacts for human review. They reduce context overload and make the included evidence auditable.

## Validation Rules

- `research_packet` requires `packet_status='valid'` and `qa_status='passed'`.
- `macro_context` requires `packet_status='valid'`.
- `senior_memo` requires `memo_status='valid'` and `qa_status='passed'`.
- `order_ticket` is context only, never instruction.
- `execution` is history/context only.
- Unknown item types are rejected.
- Missing upstream item IDs make the package invalid.
- More than `MAX_CONTEXT_ITEMS` fails validation.
- At or above `CONTEXT_BUDGET_WARNING_ITEMS` produces a warning.

## Budget Estimate

Stage 5 uses a deterministic local estimate from stored item title and summary length. It does not use a model tokenizer or external service.

## Report Boundary

Every context package report states:

```text
This context package is not order authority.
It cannot create, approve, size, validate, or execute trades.
```
