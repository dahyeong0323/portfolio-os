# Stage 9 Context Explorer API Contract

Stage 9 adds read-only context explorer endpoints for Mission Control. These endpoints expose existing Portfolio OS research, macro, senior memo, governance, canary, health, and context-package records through shaped JSON responses.

## Authority Boundary

- These endpoints are read-only `GET` endpoints only.
- They do not create orders, approve tickets, execute trades, call brokers, run LLM generation, or mutate SQLite rows.
- Returned report links are opaque report references only. The frontend must open them through `/reports?reference=...` and the Stage 8 Reports Center.
- Detail payloads are rendered as inert text/JSON by the frontend. They must not be rendered as executable HTML.

## Endpoints

### `GET /api/v1/research`

Returns:

- `count`
- `items[]`
  - `research_id`
  - `title`
  - `subject`
  - `instrument`
  - `thesis`
  - `status`
  - `created_at`
  - `updated_at`
  - `linked_report_reference`
  - `anti_thesis_present`
  - `available_actions`
  - `blocked_actions`

### `GET /api/v1/research/{research_id}`

Returns:

- `metadata`
- `thesis`
- `anti_thesis`
- `sources`
- `evidence_summary`
- `linked_reports`
- `read_only_explanation`
- `available_actions`
- `blocked_actions`

Unknown IDs return structured `404` with code `research_not_found`.

### `GET /api/v1/macro`

Returns:

- `count`
- `items[]`
  - `macro_id`
  - `title`
  - `regime`
  - `scenario`
  - `tags`
  - `created_at`
  - `linked_report_reference`
  - `available_actions`
  - `blocked_actions`

### `GET /api/v1/macro/{macro_id}`

Returns:

- `metadata`
- `regime`
- `scenario`
- `tags`
- `linked_reports`
- `read_only_explanation`
- `available_actions`
- `blocked_actions`

Unknown IDs return structured `404` with code `macro_context_not_found`.

### `GET /api/v1/senior-memos`

Returns:

- `count`
- `memos[]`
  - `memo_id`
  - `title`
  - `linked_intent_id`
  - `ticket_id`
  - `risk_validation_id`
  - `recommendation_summary`
  - `created_at`
  - `linked_report_reference`
  - `available_actions`
  - `blocked_actions`

### `GET /api/v1/senior-memos/{memo_id}`

Returns:

- `metadata`
- `input_bundle`
- `sections`
- `decision_candidates`
- `no_action_alternatives`
- `opposing_arguments`
- `linked_reports`
- `read_only_explanation`
- `available_actions`
- `blocked_actions`

Unknown IDs return structured `404` with code `senior_memo_not_found`.

### `GET /api/v1/governance`

Returns:

- `context_package_status`
- `canary`
- `health`
- `stale_context_warnings`
- `governance_report_references`
- `canary_report_references`
- `health_report_references`
- `context_report_references`
- `available_actions`
- `blocked_actions`

### `GET /api/v1/governance/events`

Returns:

- `count`
- `events[]`
  - `event_id`
  - `event_type`
  - `event_scope`
  - `severity`
  - `related_table`
  - `related_id`
  - `event_summary`
  - `created_at`

## Safe Report References

Frontend links are shown only for references matching:

- `report_[A-Za-z0-9_-]+`
- `DEMO-REPORT-[A-Za-z0-9_-]+`

Path-like values, absolute paths, and malformed references are not linked.

## Mock Fallback

The frontend mock fallback includes clearly fake `[샘플]` and `DEMO-*` data for Stage 9 surfaces. Mock data is not official portfolio evidence.

