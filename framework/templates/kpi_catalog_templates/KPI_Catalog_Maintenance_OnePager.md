# KPI Catalog Maintenance (One Page)

Purpose: Keep the KPI Catalog customer-ready, tool-agnostic, and consistent with the Golden Thread.

## 1) Strategic vs Supporting KPIs

- Strategic KPIs: decision-critical, used to steer the business.
- Supporting KPIs: explanatory or diagnostic; they must not trigger Action Codes.

## 2) Minimal required fields

Each KPI entry must include:
- `kpi_id`, `kpi_key`, `kpi_type`, `impact_dimension`, `domain_tag`, `calc_type`
- `business` section (purpose, definition, grain_scope, unit_format, interpretation)
- `technical` section (semantic measure name, dependencies, lineage)
- `governance` section (owners, review_cycle, validation, qa_rules, version)
- `metadata_quality` (completeness_score, last_review)

## 3) Golden Thread alignment

Each KPI must trace to at least one use case and fit its impact dimension and domain tags.
Do not redefine KPI meaning outside the catalog.

## 4) Change and review (lightweight)

- Update business meaning first; technical details follow the measure dictionary.
- Keep updates small and explicit; record version bumps in governance.
- Review on the defined cadence; avoid one-off exceptions.

## 5) What not to add

- Tool-specific expressions or logic
- Helper or performance-only measures
- Report/UI calculations

Result: The catalog stays stable, readable, and easy to maintain.
