# MCP Task Guides (Rezepte)

## Build Measures (from KPI Catalog)
- Inputs
  - Use Case Spec: `usecases/{cluster}/{ID}_{Slug}/spec.yaml`
  - KPI Catalog: `/_includes/kpi_catalog/*.md`
  - Model (TMDL/PBIP) path/reference
- Steps
  - Validate spec.yaml (schemas/report_spec.schema.yaml)
  - Coverage check: required_measures ∈ KPI Catalog (tools/coverage)
  - For each missing measure in TMDL:
    - Create TMDL measure from catalog (name/display_name, dax_expression, formatString, displayFolder, description)
    - Set `displayFolder` per taxonomy (e.g., 01_Sales, 02_Margin, 10_Time Intelligence, 99_QA)
  - Apply semantic model best practices (schemas/best_practices/bpa-rules-semanticmodel.json)
  - Lint model (schemas/lint.rules.yaml)
  - Ensure Descriptions/FormatStrings are present for Amount/%/Integer

## Build Report (from Report Spec)
- Inputs
  - Use Case Spec: `usecases/{cluster}/{ID}_{Slug}/spec.yaml`
  - Dataset model_ref (PBIP semantic model)
  - theme_ref, template_ref (externes Projekt)
- Steps
  - Create pages from spec (Overview/Drivers/Details)
  - Add visuals per type with bindings (value/x/y/category/series)
  - Apply formatting defaults (precision, displayUnits, legends/titles, tooltips)
  - Add slicers/navigation as defined
  - Apply theme_ref and template_ref
  - Validate against PBIR_Schema_Reference.md (structure/parts)
  - Apply report best practices (schemas/best_practices/bpa-rules-report.json)

## Improve Model (against Best Practices)
- Inputs: TMDL model
- Steps
  - Enforce Allowed Subset (schemas/TMDL_Allowed_Subset.md)
  - Apply semantic BPA rules (schemas/best_practices/bpa-rules-semanticmodel.json)
  - Fix: descriptions (Tables/Columns/Measures), formatString, displayFolder
  - Hide technical columns by pattern (*Key, *_id); set SortByColumn for labels
  - Set DataCategory (Currency/Geo/URL) where applicable
  - Relationships: single‑direction M:1 by default; document exceptions
  - QA measures (folder 99_QA), RI >= 99.9 %

## Build Alignment Map
- Inputs: `/_includes/strategy.yaml`, Use Case Front‑Matter (supports_strategic_kpi)
- Steps
  - Parse strategy.yaml → list strategic KPIs
  - Map to Use Cases (front‑matter) and render `_includes/Strategic_Alignment_Map.md`

## Precedence & Gates
- Precedence: TMDL Allowed Subset → BPA rules → Use Case Spec
- Gates: Schema valid, Coverage OK, Lint OK, BPA without Errors, QA green

