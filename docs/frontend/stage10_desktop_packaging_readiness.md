# Stage 10 Desktop Packaging Readiness

Stage 10 did not install or scaffold Tauri.

Repository inspection found no existing Tauri application scaffold such as `src-tauri`, `tauri.conf.json`, or `@tauri-apps/*` dependencies in the frontend. Because native tooling and dependency installation were not required to complete Stage 10, packaging was documented rather than forced.

## Recommended Future Packaging Constraints

If Portfolio OS is packaged with Tauri later:

- Do not enable a shell plugin.
- Do not grant arbitrary filesystem access.
- Do not store broker credentials in the frontend or Tauri layer.
- Do not add broker write, automatic order, or automatic execution capabilities.
- Load the Vite frontend as a local app shell.
- Talk only to a configured local FastAPI endpoint.
- Keep a visible local-only app mode.
- Keep mock fallback clearly labelled as `[샘플]` / `DEMO-*`.
- Treat report and context content as inert text.
- Keep the Stage 8 Reports Center opaque-reference rules.

## Suggested Future Commands

These are future packaging notes only, not implemented Stage 10 commands:

```powershell
cd frontend
npm.cmd install @tauri-apps/cli @tauri-apps/api
npm.cmd run tauri dev
npm.cmd run tauri build
```

Before adding those commands, define exact Tauri permissions and verify that no shell, arbitrary file access, secret storage, or broker capability is introduced.

## Current State

The frontend remains a Vite React app served from `frontend/`.

Validated commands for the current app:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```
