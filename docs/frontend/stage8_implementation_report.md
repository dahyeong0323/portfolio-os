# Frontend Stage 8 Implementation Report

## Implemented

- Added a read-only report registry in `portfolio_os.api.reports`.
- Added FastAPI report schemas and router endpoints:
  - `GET /api/v1/reports/categories`
  - `GET /api/v1/reports`
  - `GET /api/v1/reports/{report_reference}`
  - `GET /api/v1/reports/{report_reference}/download`
- Registered the reports router without changing Stage 1 through Stage 7 endpoints.
- Added frontend report response types and GET-only query helpers.
- Added `/reports` route and enabled the existing Reports Center sidebar item.
- Added a Reports Center UI with category filtering, report list, metadata panel, copy action, safe download link, and plaintext report viewer.
- Added Dashboard recent reports integration.
- Added Journal detail linked-report display when safe report references already exist in journal context.
- Extended mock GET fallback with clearly fake `[샘플]` and `DEMO-*` report records.

## Backend Behavior

The report registry scans only known directories:

- Reconciliation, risk validation, order ticket, senior memo, research, macro, governance, canary, context package, and health report directories under the configured exports root.
- Frontend stage Markdown documents under `docs/frontend`.

Report references are server-generated opaque values. Detail and download requests decode the reference, validate the category, validate that the filename is a plain local filename, reject unsupported suffixes, and resolve only through the configured category directory. The API does not expose absolute paths.

The download endpoint returns only registry-resolved files with Markdown or JSON media types. Reports remain read-only and no endpoint accepts POST, PUT, PATCH, or DELETE.

## Frontend Behavior

The `/reports` page shows:

- Authority boundaries stating that reports are audit/review material, not order authority.
- A category panel with clean empty states.
- A report table with title, category, format, generated time, linked object, and read-only status.
- A viewer that renders content inside a plaintext `pre`.
- Copy and download controls only for report content already returned by the backend.

The Dashboard shows recent reports with links to the Reports Center. The Journal detail page shows linked report references only when journal context already contains a safe `report_reference` or `report_references` value.

## Safety Properties

- React does not read SQLite directly.
- React does not call the Portfolio OS CLI.
- The API does not call the CLI or parse CLI stdout.
- The API does not expose arbitrary file reads.
- The frontend ignores path-like report references in UI controls.
- HTML-like report content is rendered as inert text.
- No broker write path, automatic trading, order creation, approval, rejection, execution, or reconciliation confirmation was added.
- No migrations were added for Stage 8.

## Verification

Verification completed on June 19, 2026:

- `python -m pytest tests\integration\test_frontend_stage8_reports_api.py -q`: passed, 4 tests.
- `python -m compileall -q src tests`: passed.
- `python -m pytest -q`: passed, 101 tests, 1 warning from `python_multipart` import deprecation in Starlette.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run lint`: passed.
- `npm.cmd run test`: passed, 9 files and 40 tests.
- `npm.cmd run build`: passed.
- Safety search on `frontend/src` for direct SQLite access, CLI subprocess usage, and prohibited direct-trade strings: passed.
- Runtime smoke with local FastAPI and Vite:
  - `GET http://127.0.0.1:8000/api/v1/reports/categories`: HTTP 200.
  - `GET http://127.0.0.1:8000/api/v1/reports?category=reconciliation&format=markdown&limit=1`: HTTP 200.
  - `GET http://127.0.0.1:5173/reports`: HTTP 200.
- In-app browser verification for `/reports`:
  - 1440x900: populated report rows, plaintext report content, no `<img>` execution, no prohibited direct-trade controls, no horizontal overflow.
  - 375x812: populated report rows, viewer present, no prohibited direct-trade controls, no horizontal overflow.

The broader repository contains an existing deep-research document that lists prohibited direct-trade strings as examples of what not to add; Stage 8 did not add those controls to the frontend source.

## Intentionally Missing

- Authentication, authorization, and role-based report access.
- Persistent report indexing in SQLite.
- Arbitrary filesystem browsing.
- Markdown-to-HTML rendering.
- Report generation.
- Report deletion, mutation, approval, or execution actions.
