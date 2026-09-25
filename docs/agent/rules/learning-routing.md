# Learning Routing (where to store fixes)

Goal: the same error must not recur in a new session. Every learned fix is routed to its
single source of truth (SSOT), and the relevant validation is re-run. This refines the
generic "Learning Loop" in `AGENTS.md`.

## 1. Read early (before starting implementation)

- `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` — error symptom → root cause → fix recipes.
- `core/kpi_catalog/planned.yaml` — catalog KPIs whose measure is not yet implemented in TMDL;
  the catalog↔TMDL drift check (`tooling/validation/check_catalog_tmdl_drift.py`) reports them
  as warnings, not errors.

## 2. Route new learning by error type

- **Catalog↔TMDL drift fails (strict) because a catalog measure is missing in `_Measures.tmdl`
  and is intentionally not implemented yet:**
  - Add or update the entry in `core/kpi_catalog/planned.yaml` with `kpi_id`, `owner`,
    `eta_date` (YYYY-MM-DD) and `reason` (one line). Schema:
    `tooling/generator/schemas/planned_kpi.schema.json`; the `kpi_id` must exist in
    `core/kpi_catalog/KPI_Catalog.md`.
  - Do not add this to `KNOWN_ERRORS_AND_FIXES.md` unless the drift-check logic itself is broken.

- **PBIR/visual binding failure — a measure `Property` in a `visual.json` is not found in the
  domain `_Measures.tmdl`:**
  - Fix the generator/orchestrator so it binds to the correct measure **display name**
    (do not only patch the generated `visual.json`).
  - Add a regression test, or update the existing measure-binding test expectations.
  - If this is a new error class or pattern: add a row to `KNOWN_ERRORS_AND_FIXES.md`.

- **TMDL/DAX/semantic-model structural issues** (`formatString`/`displayFolder` indentation,
  blank stubs, invalid naming):
  - Fix the generator output at its source.
  - If the same structural violation appears again: add a row to `KNOWN_ERRORS_AND_FIXES.md`.

- **Any other recurring failure** (schema state inconsistencies, empty decision fields,
  missing artifacts):
  - Add symptom → root cause → fix steps as a row to `KNOWN_ERRORS_AND_FIXES.md`
    (appropriate section).

## 3. Verify after edits

Always run the most relevant validation after substantive changes (from repo root):

- Core / cross-references: `.\tooling\run_stage1_checks.ps1`
- Fabric / PBIP artifacts: `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1`
  (or `.\tooling\quality\run_quality_gate.ps1` for Stage 1 + Fabric in one pass)
- Catalog↔TMDL drift: `python tooling/validation/check_catalog_tmdl_drift.py --repo-root . --strict`
