# Agent Instructions — Analytics Use Case Library

Use these instructions when editing this repository. Project rules in `.cursor/rules/` provide detailed conventions; this file gives high-level behavior.

## Use cases

- Preserve YAML frontmatter (`id`, `factsheet_type`) and required sections on Business and Technical factsheets.
- Only reference KPIs that exist in `framework/kpi_catalog/`; do not redefine KPI meaning, targets, or lineage in factsheets.
- Keep `required_kpis` (Business) and `kpi_to_measure_mapping` (Technical) consistent with the KPI catalog and with each other.
- Keep `layout_330300` (Business) aligned with `_internal/ai/schemas/layout_330300.schema.json` and page templates in `framework/templates/page_templates/`.
- When adding or changing action code references, update `usecases/UseCase_ActionCode_Map.yaml` so it stays consistent with `framework/action_codes/`.

## Framework (KPI catalog, action codes, templates)

- Respect the KPI catalog schema and structure; see `framework/kpi_catalog/` and `framework/templates/kpi_catalog_templates/`.
- Action code YAML must follow the structure in `framework/templates/action_codes/` and `_internal/ai/schemas/action_code.schema.json`; all `kpi_id` values must exist in the KPI catalog.
- Do not introduce new artifact types without alignment with `_internal/vision/framework_evolution.md`.

## Scripts and CI

- Prefer existing scripts under `_internal/tools/` (validation, generation, maintenance, Power BI MCP).
- Run PowerShell from the repository root when invoking these scripts.
- Before committing changes that touch use cases, framework, or data contracts, run Stage 1: `.\_internal\tools\run_stage1_checks.ps1`
- Schema authority: `_internal/ai/schemas/` for factsheets, action codes, data contracts, layout_330300. Structure and naming authority: `framework/templates/`, `docs/operating_model/`.

## Golden thread

- Use cases and reports **reference** governed definitions; they do **not** define KPI meaning or action logic. Single source of truth for KPIs is `framework/kpi_catalog/`; for action logic it is `framework/action_codes/`.
