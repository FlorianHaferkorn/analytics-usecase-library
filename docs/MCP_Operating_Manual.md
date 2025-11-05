# MCP Operating Manual (Agent + MCP)

Single source of truth for running the IDâ€‘first workflow from Use Case to validated KPIs, DAX measures, and optional PBIP scaffolding.

---

## Quickstart
- Pick a Use Case (FactSheet.md) and set frontâ€‘matter:
  - dataset_model, page_template (optional), segments, filters_default
  - supports_strategic_kpi_ids, required_kpi_ids
- Validate + Lint
  - Coverage: `analytics-usecase-library/tools/coverage/check_factsheet_vs_kpi.ps1 -FailOnMissing`
  - Catalog integrity: `analytics-usecase-library/tools/coverage/validate_kpi_catalog.ps1 -FailOnError`
  - DAX lint: `analytics-usecase-library/tools/lint/lint_dax.ps1 -FailOnError`
- Generate (optional)
  - DAX stubs: `analytics-usecase-library/tools/generate/generate_measures.ps1 -UseCase COM-001 -Out dist/dax`
  - PBIP page scaffolding (future): from page_template + required_kpi_ids

---

## Workflow (Variant A)
1) Author or select Use Case
   - FactSheet frontâ€‘matter is the machineâ€‘readable source (no spec.yaml)
2) Validate artifacts
   - Coverage (IDs), Catalog schema + best practices
3) DAX authoring (askâ€‘first)
   - Propose DAX where missing; on approval, write to catalog with format/folder
4) Lint DAX (Style Guide)
   - Enforce divide usage, VARâ€¦RETURN, avoid FORMAT(), etc.
5) Generate artifacts (optional)
   - DAX/TMDL stubs per UC; later: PBIP page scaffold
6) QA and iterate
   - BPA checks, coverage green, visuals validated

---

## Task Recipes
### Build Measures (from KPI Catalog)
- Resolve each `required_kpi_id` to catalog
- If `technical.dax_expression` present â†’ emit measure (name, expression, formatString, displayFolder)
- If missing â†’ propose DAX (askâ€‘first), then writeâ€‘back and emit
- Commands: `analytics-usecase-library/tools/generate/generate_measures.ps1 -UseCase <UC>`

### Build Report (PBIP, optional)
- Use `page_template` to place KPI cards (from `required_kpi_ids`) and slicers (`segments`)
- Apply `filters_default` at page level
- Follow `docs/PBIR_Schema_Reference.md`

### Improve Model (Best Practices)
- Apply semantic/report BPA JSONs in `schemas/best_practices/`
- Ensure descriptions, formatString, displayFolder are present; hide technical columns; set SortByColumn where needed

### Build Alignment Map
- Use `_includes/strategy.yaml` + Use Case frontâ€‘matter to render `_includes/Strategic_Alignment_Map.md`

---

## Rules & Validators
- KPI Catalog schema: `/_includes/kpi_catalog/SCHEMA.md`
- Best practices:
  - Semantic model: `schemas/best_practices/bpa-rules-semanticmodel.json`
  - Report: `schemas/best_practices/bpa-rules-report.json`
  - DAX Style: `schemas/best_practices/bpa-rules-dax.json`
- Linters & checks:
  - Coverage: `analytics-usecase-library/tools/coverage/check_factsheet_vs_kpi.ps1`
  - Catalog validator: `analytics-usecase-library/tools/coverage/validate_kpi_catalog.ps1`
  - DAX lint: `analytics-usecase-library/tools/lint/lint_dax.ps1`

---

## Precedence & Definition of Done
Precedence: Validators/Best Practices â†’ Catalog entries â†’ Use Case frontâ€‘matter.

DoD (Autoâ€‘Reportâ€‘Ready):
- FactSheet frontâ€‘matter complete (IDs, segments, filters, data_requirements if used)
- All `required_kpi_ids` resolvable; DAX present or approved; formats/folders set
- (Optional) PBIP page scaffolded; slicers + defaults applied
- BPA checks pass; coverage green; DAX lint has no errors


