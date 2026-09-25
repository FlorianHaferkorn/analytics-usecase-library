# Fabric and Power BI Validation

Run Fabric-specific checks for TMDL syntax, DAX best practices, measure dictionary alignment, and diagram layout.

## Workflow

1. **Run Fabric checks**:
   ```powershell
   .\products\fabric/powerbi\tooling\run_fabric_checks.ps1
   ```
2. **Check types**:
   - TMDL syntax validation
   - PBIP readiness
   - Diagram layout validation (spaghetti principle)
   - Measures vs KPI catalog alignment
   - TMDL vs measure dictionary consistency
   - DAX best practices (via BPA rules)
3. **On failure, diagnose**:
   - **Measures vs KPI**: KPI IDs in measure dictionary don't match catalog → fix `core/semantic_models/domains/*.yaml` measure dictionary OR add KPI to catalog.
   - **TMDL vs dictionary**: Measures in TMDL don't match dictionary → regenerate TMDL or update dictionary.
   - **Diagram layout**: Model view layout violates spaghetti principle → fix `diagramLayout.json` (see layout rules below).
   - **TMDL syntax**: Indentation or syntax error → check tabs-only indentation, no `:=` in DAX.
4. **For regeneration**:
   ```powershell
   .\tooling\generator\generate_tmdl_measures.ps1 -UseCase <id>
   # OR for all use cases: run orchestrate_full_model.ps1
   .\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1
   ```

## TMDL rules

- **Indentation**: Use **TABS only** (spaces cause parser errors).
- **Levels**: Table properties = 1 tab; column/measure properties = 2 tabs; nested = 3 tabs.
- **Numeric columns**: Must have `summarizeBy: none` (prevents unintentional aggregation).
- **Measures**: Use `formatString`, `displayFolder`, `lineageTag`, `isHidden`; describe with a `///` block above the measure (TMDL's description syntax, read by Copilot, essentials in the first 200 chars) — never a `description:` key.
- **DAX**: No `:=` operator (DAX uses `=` only).

## Diagram layout (spaghetti principle)

Required layout for `diagramLayout.json`:
- **`_Measures` table**: Top-left corner at (x=0, y=0)
- **Fact tables**: Horizontal row at y=0, starting x=280, spaced 250px apart (x=280, 530, 780, ...)
- **Dimension tables**: Vertical column at x=0, starting y=120, spaced 120px apart (y=120, 240, 360, ...)
- **Security tables**: Include in left column with dimensions

Validated by `check_diagram_layout.ps1` (part of Fabric checks).

## Guardrails

- TMDL files: tabs-only indentation (use "Convert Indentation to Tabs" in editor if needed).
- DAX syntax: `=` for measures, never `:=`.
- Measure dictionaries: `core/semantic_models/domains/<domain>_measures.yaml` must align with `core/kpi_catalog/`.
- Regenerate TMDL after dictionary changes to keep them in sync.
- Run Fabric checks before committing Power BI output.

## Key paths

- Fabric checks: `products/fabric/powerbi/tooling/run_fabric_checks.ps1`
- TMDL output: `products/fabric/powerbi/dist/<UseCase>/`
- Measure dictionaries: `core/semantic_models/domains/`
- KPI catalog: `core/kpi_catalog/`
- BPA rules: `tooling/linters/powerbi/bpa-rules-tmdl.json`
