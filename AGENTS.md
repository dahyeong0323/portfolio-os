# Portfolio OS Agent Instructions

## Always Create Stage Handoff Files

After completing any Portfolio OS stage implementation, always create a handoff document for the next stage.

Required path format:

```text
docs/stage<N>_handoff_for_stage<N+1>.md
```

The handoff must be factual and based only on implemented code, migrations, tests, generated reports, and existing project documents.

Each handoff must explain:

- what the completed stage implemented
- which outputs and interfaces are stable
- what the next stage may consume
- what the next stage must not bypass
- preserved invariants from earlier stages
- known limitations or intentionally missing functionality
- verification status, including tests and generated reports

Do not invent future-stage functionality in a handoff.

## Project Safety Rules

- Do not move existing root project documents unless the user explicitly asks.
- Do not modify earlier-stage migrations when implementing a later stage.
- Add new migrations only for the current stage.
- Keep runtime dependencies standard-library only unless the user explicitly approves a dependency change.
- Keep `pytest` as the only development dependency unless explicitly approved.
- Treat Stage 1 ledger truth and Stage 2 risk/ticket workflow as upstream gates for later stages.
