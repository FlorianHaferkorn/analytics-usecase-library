# MCP Playbook — Agent Execution Recipe (Variant A)

Purpose: Deterministic, ID‑first flow to turn Use Case FactSheets + KPI Catalogs into a working PBIP report (theme/layout optional).

---

## Artifacts (Inputs)
- Use Case folders: `usecases/{cluster}/{ID_Title}/`
  - `FactSheet.md`: front‑matter is the machine‑readable source (no spec.yaml)
    - required_kpi_ids, required_kpis, segments, filters_default, qa_asserts
    - data_requirements (facts/dims/relationships), model_mapping (labels → fields)
    - dataset_model (name/path), page_template (future use for visuals)
- KPI Catalogs: `/_includes/kpi_catalog/*.md` (YAML blocks per KPI)
- Best Practices:
  - Semantic model: `schemas/best_practices/bpa-rules-semanticmodel.json`
  - Report: `schemas/best_practices/bpa-rules-report.json`
- PBIR reference: `docs/PBIR_Schema_Reference.md`
- Strategic overview (business): `/_includes/Strategic_KPIs.md`

---

## Precedence (conflicts)
1) Schema/linters (ID format, required fields) + best practices
2) Catalog entries (technical truth: formatString, displayFolder, descriptions)
3) Use Case front‑matter (selection of KPIs, segments, defaults)

---

## Workflow (Human → Agent)
1) Authoring (Business/Analyst): Fill FactSheet front‑matter + business sections
2) Catalog Enrichment (Data/BI): Ensure all referenced KPI IDs have complete technical blocks
3) Build (Agent): validate → build_measures → build_report → qa

---

## Steps (Agent)
1) Read Use Case:
   - Parse FactSheet front‑matter (required_kpi_ids, segments, filters_default, data_requirements, model_mapping, dataset_model, page_template)
2) Validate:
   - Coverage IDs → Catalog: `tools/coverage/check_factsheet_vs_kpi.ps1 -FailOnMissing`
   - Catalog schema: `tools/coverage/validate_kpi_catalog.ps1 -FailOnError`
   - Data requirements: ensure facts/dims/relationships fields are present or scaffoldable
3) Build Measures (TMDL):
   - For each `required_kpi_id` resolve catalog entry
   - If `technical.dax_expression` present → create/patch measure (name, expression, formatString, displayFolder, description)
   - If expression missing → use safe templates (Δ, Δ%, LY, CCC) based on ID pattern
   - Persist to PBIP/TMDL in `dataset_model`
4) Build Report (PBIR):
   - Scaffold one page using `page_template` (if provided) or a default
   - Add visuals per KPI, slicers from `segments`, apply `filters_default`
   - Follow `docs/PBIR_Schema_Reference.md` for structure
5) Quality (QA):
   - Apply semantic BPA: `schemas/best_practices/bpa-rules-semanticmodel.json`
   - Apply report BPA: `schemas/best_practices/bpa-rules-report.json`
   - Emit a build log (coverage results, BPA violations, created measures/pages)

---

## Commands (reference)
- Coverage (ID‑only):
  - `tools/coverage/check_factsheet_vs_kpi.ps1 -FailOnMissing`
- Catalog validation:
  - `tools/coverage/validate_kpi_catalog.ps1 -FailOnError`
- BPA (conceptual; tool/host dependent):
  - Model: apply `bpa-rules-semanticmodel.json` to measures/model objects
  - Report: apply `bpa-rules-report.json` after page creation

---

## Definition of Done (Auto‑Report‑Ready)
- FactSheet front‑matter complete (IDs, segments, filters, data_requirements, model_mapping)
- All `required_kpi_ids` resolvable in catalogs; measures generated/updated with format/metadata
- One PBIR page scaffolded; visuals wired; slicers + default filters applied
- BPA checks pass without blockers; coverage is green

---

## Notes
- IDs are canonical (ASCII); human names (kpi_key) may include symbols (Δ, ±, €)
- Themes/layouts are outside this repo; can be linked later via template/theme refs
- Use `docs/Business_Playbook.md` for non‑technical guidance; `docs/Quickstart_1-Pager.md` for a one‑screen summary
