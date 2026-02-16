---
name: stage1-pre-commit
description: Run Stage 1 CI checks before committing. Use when the user is about to commit, asks to run checks, validation, or mentions Stage 1, pre-commit gate, or CI checks.
---

# Stage 1 Pre-Commit Check

Run the mandatory CI hard gate before committing any changes to use cases, framework artifacts, or data contracts.

## Workflow

1. **Ensure repo root**: Change to repository root before running.
2. **Check schema validation prerequisite** (one-time):
   - If `check_schema_validation.ps1` fails with module errors, run:
     ```powershell
     cd tooling\validation
     npm ci
     cd ..\..
     ```
3. **Run Stage 1**:
   ```powershell
   .\tooling\run_stage1_checks.ps1
   ```
4. **On failure**: Stop immediately. Do not suggest workarounds. Use the `fix-stage1-failure` skill to diagnose and fix the specific failing check.
5. **On success**: All checks passed; changes are safe to commit.

## Stage 1 checks (in order)

1. `check_schema_validation.ps1` — JSON schema validation (action codes, brackets, org_roles)
2. `validate_factsheets.ps1` — Factsheet structure + bracket existence
3. `check_factsheet_vs_kpi.ps1` — KPI references exist in catalog
4. `validate_kpi_catalog.ps1` — KPI catalog structure
5. `check_action_codes_vs_kpi.ps1` — Action code KPI references exist
6. `check_factsheet_action_codes.ps1` — Action code references valid
7. `check_decision_spines.ps1` — Decision spine consistency
8. `check_duplicate_ids.ps1` — No duplicate IDs
9. `check_ssot_markers.ps1` — SSOT markers valid
10. `check_docs_refs.ps1` — Doc references valid
11. `check_forbidden_content.ps1` — No forbidden content

## Guardrails

- Always run from repository root.
- Stage 1 is non-negotiable; all checks must pass before merge.
- First failure stops the suite; fix that check before continuing.
- If schema validation fails repeatedly, verify Node.js dependencies are installed in `tooling/validation/`.
