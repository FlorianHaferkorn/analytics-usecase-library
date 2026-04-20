# Agent Instructions — Analytics Use Case Library

Canonical agent rules and skills live in `docs/agent/` (tool-agnostic Markdown). Tool-specific wrappers are **generated** — do not edit them directly:

| Tool | Generated files | Generator |
|------|----------------|-----------|
| Cursor | `.cursor/rules/*.mdc`, `.cursor/skills/*/SKILL.md` | `python tooling/agent/generate_tool_configs.py` |
| VS Code Copilot | `.github/copilot-instructions.md` | same generator |
| Claude Code | This file (`AGENTS.md`) | maintained manually |

## Use cases

- Preserve YAML frontmatter (`id`, `factsheet_type: business`) and required sections on Business Factsheets; preserve UseCase_Bracket.yaml structure per schema.
- Only reference KPIs that exist in `core/kpi_catalog/`; do not redefine KPI meaning, targets, or lineage in factsheets or brackets.
- Business Factsheets are prose-only (Lean 2.0); all machine-readable config is in `UseCase_Bracket.yaml` (orchestration, governance, value driver model, UX layout rules). The bracket is the source for the **report bill-of-materials (BoM)**: KPIs (strategic, influencing, optional supporting_kpi_ids), evidence grain (`ux_layout_rules.page_2_execution.component_300s.evidence_grain`), and data contract (`overrides.data_contract_ref`). The registry validates KPI completeness (closure under catalog depends_on_measures) and evidence grain against domain contracts. Evidence grain is defined only in the bracket; action codes do not prescribe or imply report grain.
- Keep `layout_330300` (if used) aligned with `tooling/generator/schemas/layout_330300.schema.json` and page templates in `core/templates/page_templates/`.
- When adding or changing action code references, update the `orchestration.action_code_ids` list in each use case's `UseCase_Bracket.yaml` so it stays consistent with `core/action_codes/`.

## Framework (KPI catalog, action codes, templates)

- Respect the KPI catalog schema and structure; see `core/kpi_catalog/` and `core/templates/kpi_catalog_templates/`.
- Action code YAML must follow the structure in `core/templates/action_codes/` and `tooling/generator/schemas/action_code.schema.json`; all `kpi_id` values must exist in the KPI catalog.
- Do not introduce new artifact types without alignment with `internal/archive/framework_evolution.md`.

## Scripts and CI — Three Independent Gates

| Gate | Scope | Command |
|------|-------|---------|
| **Stage 1 (Core)** | `core/`, `tooling/`, `docs/` — tool-agnostic only | `./tooling/run_stage1_checks.ps1` |
| **Fabric Gate** | `products/fabric/` — TMDL, DAX, PBIP, measures | `./products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| **OSS Gate** | `products/open_source_stack/` — Evidence, dbt, adapter | `bash products/open_source_stack/tooling/run_oss_checks.sh` |

- Prefer existing scripts under `tooling/` (validation, generation, maintenance). Fabric pipeline: `products/fabric/powerbi/orchestrator/`.
- Run PowerShell from the repository root when invoking these scripts.
- Before committing changes that touch use cases, framework, or data contracts, run **Stage 1**. For Fabric/Power BI output validation, run the **Fabric Gate**. For OSS stack changes, run the **OSS Gate**.
- Run `.\tooling\maintenance\sync_evidence_grain_note_to_factsheet.ps1` after adding or changing `overrides.evidence_grain_note` in a bracket.
- Schema authority: `tooling/generator/schemas/` for factsheets, action codes, data contracts, layout_330300. Structure and naming authority: `core/templates/`, `core/strategy_operating_model/operating_model/`.

## Golden thread

- Use cases and reports **reference** governed definitions; they do **not** define KPI meaning or action logic. Single source of truth for KPIs is `core/kpi_catalog/`; for action logic it is `core/action_codes/`.

## Skills (tool-agnostic)

Reusable workflows for AI agents and humans. Each skill describes a complete workflow with validation, error handling, and learning loop. All skills live in `docs/agent/skills/` and can be used by any AI tool (Claude Code, Cursor, Copilot, etc.).

### Core skills

| Skill | When to use |
|-------|-------------|
| [`add-usecase-scaffold`](docs/agent/skills/add-usecase-scaffold.md) | Create a new use case with Business Factsheet and UseCase_Bracket |
| [`edit-factsheet-safely`](docs/agent/skills/edit-factsheet-safely.md) | Edit Business factsheets without breaking Stage 1 |
| [`edit-usecase-bracket-safely`](docs/agent/skills/edit-usecase-bracket-safely.md) | Edit UseCase_Bracket.yaml without breaking orchestration |
| [`add-kpi-reference-safely`](docs/agent/skills/add-kpi-reference-safely.md) | Add a KPI reference only if it exists in the catalog |
| [`add-action-code-and-wire-up`](docs/agent/skills/add-action-code-and-wire-up.md) | Create/update action codes and wire them into use cases |
| [`assess-change-impact`](docs/agent/skills/assess-change-impact.md) | Assess blast radius before renaming/deleting IDs |
| [`fix-stage1-failure`](docs/agent/skills/fix-stage1-failure.md) | Diagnose and fix Stage 1 CI failures |
| [`stage1-pre-commit`](docs/agent/skills/stage1-pre-commit.md) | Run Stage 1 checks before committing |

### Fabric / Power BI skills

| Skill | When to use |
|-------|-------------|
| [`generate-and-validate-pbi-report`](docs/agent/skills/generate-and-validate-pbi-report.md) | Generate Power BI reports with iterative validation |
| [`fix-pbi-report-errors`](docs/agent/skills/fix-pbi-report-errors.md) | Diagnose and fix Power BI report / semantic model errors |
| [`fabric-powerbi-validation`](docs/agent/skills/fabric-powerbi-validation.md) | Validate Fabric output (TMDL, DAX, measures) |

### OSS stack skills

| Skill | When to use |
|-------|-------------|
| [`generate-oss-dashboard`](docs/agent/skills/generate-oss-dashboard.md) | Generate Evidence.dev dashboard pages from IR and bracket |
| [`fix-oss-dashboard-errors`](docs/agent/skills/fix-oss-dashboard-errors.md) | Diagnose and fix Evidence / OSS validation errors |
| [`oss-stack-validation`](docs/agent/skills/oss-stack-validation.md) | Validate OSS stack artifacts (adapter, pages, theme, SQL) |

**Learning loop:** After fixing any error, add a new row to `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` if the error class is not yet documented.
