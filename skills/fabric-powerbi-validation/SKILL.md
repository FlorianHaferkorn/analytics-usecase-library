---
name: fabric-powerbi-validation
description: "Validate Fabric and Power BI output (TMDL, DAX, measures). Use when working on TMDL files, DAX measures, Fabric checks, or Power BI semantic models."
version: "1.0.0"
license: MIT
source: ALUCA (Analytics Library of Use Cases) — governance overlay
---

<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; run tooling/generator/generate_tool_configs.py -->

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

## MCP servers and new DAX functions (Microsoft Learn, read 2026-10-01)

- **Which MCP server** (Learn `power-bi/developer/mcp/mcp-servers-overview`):
  - Build or validate a model: **Power BI Authoring MCP**. Local is generally available
    (`stdio`, the npm package pinned in `.mcp.json`, reaches PBIP/TMDL under `dist/`, supports a
    service principal). Hosted is preview (`https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring`,
    Fabric workspaces only). This repo uses the local server; setup:
    `products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md`.
  - Ask questions of a deployed model as a consumer: **Fabric IQ MCP** (generally available,
    read-only, delegated sign-in only, no service principal; Learn `fabric/iq/connectors/fabric-iq-mcp`).
    Not a step of the agentic loop; its role as a manual cross-check for S4 is assessed in
    `docs/plans/UMSETZUNGSPLAN_AGENTIC_LOOP.md` (AP-4).
  - Learn warns against using the authoring server for consumption.
- **`TEXTCONTAINS` / `TEXTSIMILARITY`** (new in September 2026; Learn `dax/textcontains-function-dax`,
  `dax/textsimilarity-function-dax`): full-text match (Boolean) and relevance score on a string
  column; modes `TEXTMATCHING`, `FUZZYMATCHING`, `PHRASEMATCHING`.
  - They need a persisted full-text index on the column: TMDL column property
    `fullTextIndexingBehavior: full` (or `explicit`), then a refresh (Learn
    `analysis-services/azure-analysis-services/full-text-indexing`, preview). Import, Dual and Direct
    Lake only; pure DirectQuery fails.
  - Stemming follows the model culture (`de` and `en` are supported, which covers the `de-DE` and
    `en-US` models in `dist/`).
  - **Do not emit them yet.** `fullTextIndexingBehavior` is not in
    `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md` and no use case is known to
    need free-text search (ASSUMPTION, unchecked). Adopting it is a separate decision (subset, generator, BPA).
  - Nothing breaks today: `tooling/` holds no DAX function allowlist that would reject the new names
    (grep, 2026-10-01).

## Key paths

- Fabric checks: `products/fabric/powerbi/tooling/run_fabric_checks.ps1`
- TMDL output: `products/fabric/powerbi/dist/<UseCase>/`
- Measure dictionaries: `core/semantic_models/domains/`
- KPI catalog: `core/kpi_catalog/`
- BPA rules: `tooling/linters/powerbi/bpa-rules-tmdl.json`
