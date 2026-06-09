# Stage 5 CLI Usage

All commands support the global `--db` option.

## Governance

```powershell
portfolio-os seed-default-governance-policy --activate
portfolio-os activate-governance-policy --governance-policy-id 1
portfolio-os list-governance-rules
```

## Configuration And Templates

```powershell
portfolio-os capture-configuration-snapshot --name "weekly config" --as-of-date 2026-05-01
portfolio-os register-template --name context_default --type context_package
portfolio-os create-template-version --template-id 1 --version 1.0.0 --body "Template body." --default
portfolio-os activate-template-version --template-version-id 1
```

## Golden Tests And Canary

```powershell
portfolio-os create-golden-test-set --name authority --version 1
portfolio-os add-golden-test-case --golden-test-set-id 1 --name safe --type valid_context_boundary --input-text "This is context only." --expected-status passed
portfolio-os run-canary --scope system --golden-test-set-id 1
portfolio-os show-canary-run --canary-run-id 1
portfolio-os export-canary-report --canary-run-id 1
```

## Context

```powershell
portfolio-os create-context-package --name "weekly context" --scope review --as-of-date 2026-05-01
portfolio-os add-context-item --context-package-id 1 --item-type memory --item-id 1
portfolio-os validate-context-package --context-package-id 1
portfolio-os export-context-package --context-package-id 1
```

## Memory And Delta Review

```powershell
portfolio-os create-memory-item --type system_note --key rule_1 --text "Use valid upstream artifacts only."
portfolio-os list-memory-items
portfolio-os create-delta-review --name weekly_delta --previous-context-package-id 1 --current-context-package-id 2
```

## Health And Integrations

```powershell
portfolio-os capture-system-health --as-of-date 2026-05-01
portfolio-os export-system-health-report --system-health-snapshot-id 1
portfolio-os register-read-only-source --name broker_export --type broker_export --read-only-confirmed --authority-boundary-note "CSV export only."
portfolio-os record-read-only-import --integration-source-id 1 --scope statement --status recorded --rows-seen 10
```
