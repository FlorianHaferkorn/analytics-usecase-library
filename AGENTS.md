# Agent Instructions — Analytics Use Case Library

Use these instructions when editing this repository. Project rules in `.cursor/rules/` provide detailed conventions; this file gives high-level behavior.

## Use cases

- Preserve YAML frontmatter (`id`, `factsheet_type: business`) and required sections on Business Factsheets; preserve UseCase_Bracket.yaml structure per schema.
- Only reference KPIs that exist in `core/kpi_catalog/`; do not redefine KPI meaning, targets, or lineage in factsheets or brackets.
- Business Factsheets are prose-only (Lean 2.0); all machine-readable config is in `UseCase_Bracket.yaml` (orchestration, governance, value driver model, UX layout rules). The bracket is the source for the **report bill-of-materials (BoM)**: KPIs (strategic, influencing, optional supporting_kpi_ids), evidence grain (`ux_layout_rules.page_2_execution.component_300s.evidence_grain`), and data contract (`overrides.data_contract_ref`). The registry validates KPI completeness (closure under catalog depends_on_measures) and evidence grain against domain contracts. Evidence grain is defined only in the bracket; action codes do not prescribe or imply report grain.
- Keep `layout_330300` (if used) aligned with `tooling/ai/schemas/layout_330300.schema.json` and page templates in `core/templates/page_templates/`.
- When adding or changing action code references, update the `orchestration.action_code_ids` list in each use case's `UseCase_Bracket.yaml` so it stays consistent with `core/action_codes/`.

## Framework (KPI catalog, action codes, templates)

- Respect the KPI catalog schema and structure; see `core/kpi_catalog/` and `core/templates/kpi_catalog_templates/`.
- Action code YAML must follow the structure in `core/templates/action_codes/` and `tooling/ai/schemas/action_code.schema.json`; all `kpi_id` values must exist in the KPI catalog.
- Do not introduce new artifact types without alignment with `internal/archive/framework_evolution.md`.

## Scripts and CI

- Prefer existing scripts under `tooling/` (validation, generation, maintenance). Fabric pipeline (orchestrate, reports, semantic models): `products/fabric/powerbi/orchestrator/`.
- Run PowerShell from the repository root when invoking these scripts.
- Before committing changes that touch use cases, framework, or data contracts, run Stage 1: `.\tooling\run_stage1_checks.ps1`. For Fabric/Power BI output validation (measures vs KPI, TMDL vs measure dictionary), run `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` or full suite `.\tooling\run_all_checks.ps1`.
- Run `.\tooling\maintenance\sync_evidence_grain_note_to_factsheet.ps1` after adding or changing `overrides.evidence_grain_note` in a bracket (e.g. after migration or when adding a governance note).
- Schema authority: `tooling/ai/schemas/` for factsheets, action codes, data contracts, layout_330300. Structure and naming authority: `core/templates/`, `core/strategy_operating_model/operating_model/`.

## Golden thread

- Use cases and reports **reference** governed definitions; they do **not** define KPI meaning or action logic. Single source of truth for KPIs is `core/kpi_catalog/`; for action logic it is `core/action_codes/`.

## Skills (tool-agnostisch)

Wiederverwendbare Workflows für AI-Agenten und Menschen. Jeder Skill beschreibt einen kompletten Arbeitsablauf mit Validierung, Fehlerbehandlung und Lernschleife. Die Skills liegen in `internal/skills/` und können von jedem AI-Tool (Claude Code, Cursor, Copilot, etc.) verwendet werden.

| Skill | Wann verwenden |
|-------|---------------|
| [`generate-and-validate-pbi-report.md`](internal/skills/generate-and-validate-pbi-report.md) | Power BI Report erstellen, neu generieren oder nach Bracket-Änderungen aktualisieren |
| [`fix-pbi-report-errors.md`](internal/skills/fix-pbi-report-errors.md) | Fehler in bestehenden Reports oder Semantic Models diagnostizieren und beheben |

**Lernschleife:** Nach jedem behobenen Fehler **muss** eine neue Zeile in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` eingetragen werden, wenn die Fehlerklasse noch nicht dokumentiert ist. So werden Lösungen wiederverwendbar.
