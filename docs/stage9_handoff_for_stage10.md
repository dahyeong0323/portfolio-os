# Stage 9 Handoff For Stage 10

## Completed Stage 9 Scope

Stage 9 added a read-only Context Explorer for existing local Portfolio OS context records:

- Research context
- Macro context
- Senior memo context
- Governance, canary, health, and context package context

No trading, broker, automatic execution, order approval, LLM generation, or SQLite-direct-from-React behavior was added.

## Stable Backend Interfaces

The following `GET` endpoints are available under `/api/v1`:

- `/research`
- `/research/{research_id}`
- `/macro`
- `/macro/{macro_id}`
- `/senior-memos`
- `/senior-memos/{memo_id}`
- `/governance`
- `/governance/events`

Unknown detail IDs return structured 404 errors using the existing API error envelope.

## Stable Frontend Interfaces

The following routes are available:

- `/research`
- `/research/:researchId`
- `/macro`
- `/macro/:macroId`
- `/senior-memos`
- `/senior-memos/:memoId`
- `/governance`

The following hooks are available in `frontend/src/api/queries/contextExplorer.ts`:

- `useResearchItems`
- `useResearchDetail`
- `useMacroItems`
- `useMacroDetail`
- `useSeniorMemos`
- `useSeniorMemoDetail`
- `useGovernanceOverview`
- `useGovernanceEvents`

## What Stage 10 May Consume

Stage 10 may consume the shaped Stage 9 JSON responses and frontend hooks for read-only context display, linking, filtering, or dashboards.

Stage 10 may link report references through the Stage 8 Reports Center only when references match the existing safe opaque-reference rule.

## What Stage 10 Must Not Bypass

Stage 10 must not bypass:

- Stage 1 ledger truth
- Stage 2 Risk Engine and order ticket workflow
- Stage 8 Reports Center safe reference and plaintext display rules
- Backend router/schema boundaries for context records

Stage 10 must not add browser-side SQLite access, broker writes, automatic trading, direct order execution, or order approval from context explorer surfaces.

## Preserved Invariants

- Ledger truth remains upstream.
- Risk validation and ticket approval remain upstream gates.
- Reports are opened through opaque server-generated references.
- Context records are advisory/evidence surfaces only.
- Frontend report and context content is rendered inertly, not as executable HTML.
- Mock fallback data is clearly marked `[샘플]` / `DEMO-*`.

## Known Limitations

- Stage 9 does not add search, filters, pagination, or export controls for context explorers.
- Stage 9 does not create new context artifacts.
- Stage 9 does not add new migrations.
- Governance overview returns the latest package/canary/health records where present and a clean empty state where absent.
- Runtime browser verification is recorded below only if completed in this implementation pass.

## Verification Status

Completed checks:

- `python -m compileall -q src\portfolio_os\api`
- `python -m pytest tests\integration\test_frontend_stage8_reports_api.py -q`
- `python -m pytest tests\integration\test_frontend_stage9_context_explorer_api.py -q`
- `python -m compileall -q src tests`
- `python -m pytest -q` - 105 passed, 1 warning from Starlette/python-multipart import deprecation
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run test -- ContextExplorerPages.test.tsx`
- `npm.cmd run test` - 44 passed
- `npm.cmd run build`

Safety searches:

- `frontend/src` runtime source has no `Buy Now`, `Sell Now`, `Quick Trade`, `즉시 매수`, or `즉시 매도` strings outside tests.
- `frontend/src` has no direct SQLite/process access string matches for the checked patterns.
- Stage 8 Reports Center and Stage 9 Context Explorer viewers have no `dangerouslySetInnerHTML` or `innerHTML` matches.

Runtime verification:

- Vite served `/research` on `127.0.0.1:5173`.
- Browser observation of `/research` confirmed the page rendered, authority boundaries appeared, and no `img` or non-module `script` execution target was created.
- FastAPI foreground startup using `python -m uvicorn portfolio_os.api.app:app --host 127.0.0.1 --port 8010` reached application startup before the command timeout stopped it.
- Detached FastAPI runtime launch exited immediately in this local desktop/sandbox process environment, so live browser verification against a running API could not be completed.
- A later localhost browser retry was blocked by Browser Use URL policy; no workaround was attempted.
