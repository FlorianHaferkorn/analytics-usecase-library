# Agent Instructions — ALUCA (Analytics Library of Use Cases)

> **Universal entry point for all AI agents** (Claude, Cursor, Copilot, Codex, Aider, …).
> Tool-specific overrides live alongside their tool's config: Claude → `CLAUDE.md`, Cursor → `.cursor/rules/`.

---

## Golden Thread Principle

Use cases and reports **reference** governed definitions — they do not define KPI meaning or action logic.

| Source of Truth | Location |
|---|---|
| KPI definitions | `core/kpi_catalog/` |
| Action logic | `core/action_codes/` |
| Semantic model conventions | `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md` |
| Page templates | `core/templates/page_templates/` |
| Schema authority | `tooling/generator/schemas/` |

---

## Use Cases

- Preserve YAML frontmatter (`id`, `factsheet_type: business`) and required sections on Business Factsheets; preserve `UseCase_Bracket.yaml` structure per schema.
- Only reference KPIs that exist in `core/kpi_catalog/`; never redefine KPI meaning, targets, or lineage in factsheets or brackets.
- Business Factsheets are prose-only (Lean 2.0). All machine-readable config lives in `UseCase_Bracket.yaml` (orchestration, governance, value driver model, UX layout rules).
- When adding or changing action code references, update `orchestration.action_code_ids` in `UseCase_Bracket.yaml`.

---

## Framework (KPI Catalog, Action Codes, Templates)

- Respect KPI catalog schema — see `core/kpi_catalog/` and `core/templates/kpi_catalog_templates/`.
- Action code YAML must follow `core/templates/action_codes/` and `tooling/generator/schemas/action_code.schema.json`. All `kpi_id` values must exist in the KPI catalog.

---

## Scripts and CI

> **⚠️ GitHub Actions is quota-blocked until 2026-07-01.** Until then, every CI run on this
> repo fails instantly at the runner level (jobs complete in ~1s with no logs / HTTP 404) —
> regardless of the code. This affects `main` and every branch equally. **Treat all GitHub
> Actions failures before that date as infrastructure, not code defects, and do not re-run or
> "fix" them.** The authoritative gate is the **local** test suite: `python3 -m pytest -q`
> (must be green before commit). Re-validate via CI only after the quota window reopens.

Run all scripts from the **repository root**.

**PowerShell (Windows / CI):**

| Task | Command |
|---|---|
| Stage 1 (required before commit) | `.\tooling\run_stage1_checks.ps1` |
| **Quality gate (Stage 1 + Fabric)** | `.\tooling\quality\run_quality_gate.ps1` |
| Fabric / Power BI validation only | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` |
| Full suite | `.\tooling\run_all_checks.ps1` |
| Full model generation | `.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1` |

**Python / Shell (Linux / macOS / CI):**

| Task | Command |
|---|---|
| Python test suite | `python3 -m pytest tooling/tests/ products/ -q` |
| OSS stack validation | `bash products/open_source_stack/tooling/run_oss_checks.sh` |
| OSS report generation | `python3 products/oss_adapters/orchestrator/orchestrate_oss.py --bracket <path> --adapter metabase` |
| Registry build | `python3 tooling/ontology/registry_builder.py --repo-root .` |
| Health scorecard | `python3 tooling/health_scorecard.py` |
| Schema validation (Python) | `python3 -m pytest tooling/tests/ -k schema -q` |

---

## TMDL Conventions (Hard Rules)

| Rule | Correct | Wrong |
|---|---|---|
| Indentation | Tabs only | Spaces |
| DAX assignment | `=` | `:=` |
| Measure docs | `/// Purpose: ...` comment above | `description:` property |
| Numeric columns | Always include `summarizeBy: none` | Omit summarizeBy |
| Measure formatting | Always include `formatString` | Omit formatString |

**Model view layout (Spaghetti Principle):**
- `_Measures` table at position (0, 0)
- Fact tables in a horizontal row at y=0 (x: 280, 530, 780, …)
- Dimension tables in a vertical column at x=0 (y: 120, 240, 360, …)

Reference: `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md`

---

## Power BI / PBIP Development

### Fabric CLI (`fab`)

Use `fab` for all Fabric data-plane operations (workspaces, models, reports, notebooks). Use `az` for Azure infrastructure (capacity, networking, RBAC).

```bash
fab auth login                        # Authenticate (opens browser)
fab auth status                       # Verify authentication
fab config set mode command_line      # Required for agent non-interactive mode
fab ls                                # List workspaces
fab ls "MyWorkspace.Workspace"        # List items in workspace
```

**Common operations:**
```bash
# Trigger semantic model refresh
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/refreshes" -X post -i '{"type":"Full"}'
# Execute DAX query
fab api -A powerbi "groups/$WS_ID/datasets/$MODEL_ID/executeQueries" -X post \
  -i '{"queries":[{"query":"EVALUATE ROW(\"Value\", [My Measure])"}]}'
# Import PBIP to workspace
fab import "ws.Workspace/Model.SemanticModel" -i ./dist/Domain.SemanticModel -f
```

**Python utility scripts** (in `products/fabric/powerbi/tooling/scripts/`):

| Script | Purpose |
|---|---|
| `execute_dax.py` | Run DAX queries with JSON/CSV/ASCII output |
| `search_across_workspaces.py` | Cross-workspace item search via DataHub V2 API |
| `create_direct_lake_model.py` | Create Direct Lake semantic model from lakehouse tables |

### PBIR Report Development

Reference docs: `products/fabric/powerbi/docs/references/`

| Doc | When to use |
|---|---|
| `pbir-visual-json.md` | Editing visual.json files directly (position, expressions, data binding) |
| `pbir-conditional-formatting.md` | Adding measure-based, gradient, or rules-based conditional formatting |
| `pbir-theme.md` | Modifying theme.json (colors, fonts, wildcard inheritance) |
| `pbir-extension-measures.md` | Report-layer DAX in reportExtensions.json for rapid formatting iteration |
| `tmdl-tom-object-types.md` | Programmatic semantic model editing via TOM/PowerShell |

**Extension measures** (report-layer DAX escape hatch):
- Use for formatting/color logic that doesn't need model-level reuse
- Store in `ReportName.Report/definition/reportExtensions.json`
- Delete the file entirely when empty (empty file causes deserialization errors)
- Visual references require `"Schema": "extension"` in the `SourceRef`
- Promotion path: once stable, move to the semantic model's `_Measures` table

### Report Page Structure

Every use case gets exactly 2 pages:
1. **Overview** (3-30 second layer): KPI cards, date slicer, trend, variance, drivers
2. **Detail** (300 second layer): Slicer pane, smart narrative, detail matrix, optional action panel

Page types: T1 Strategic Overview, T2 Tactical Variance, T3 Operational Monitoring, T4 Prescriptive Recommendation.

Layout template: `core/templates/page_templates/Page_Spec_3_30_300.md`

---

## Open Source Stack & OSS Adapters

### `products/open_source_stack/` — Evidence.dev (full stack)

| Path | Purpose |
|---|---|
| `tooling/validate_oss.py` | Validates OSS artifacts against schema |
| `tooling/run_oss_checks.sh` | Full OSS validation gate (Linux/macOS/CI) |
| `tooling/page_generator/` | Generates Evidence.dev pages from use case brackets |
| `tooling/metric_generator/` | Generates dbt metric definitions from KPI catalog |

### `products/oss_adapters/` — Grafana / Metabase / Superset (adapter stubs)

| Adapter | File | Status |
|---|---|---|
| Grafana | `tooling/adapters/grafana.py` | Stub — `render()` not yet implemented |
| Metabase | `tooling/adapters/metabase.py` | Stub — `render()` not yet implemented |
| Superset | `tooling/adapters/superset.py` | Stub — `render()` not yet implemented |

---

## Skills (reusable workflows)

Source: `docs/agent/skills/` · Condensed rules: `docs/agent/rules/`

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

---

## Learning Loop

When validation fails:
1. Read the error message carefully
2. Check `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (symptom | cause | fix)
3. Fix the root cause
4. Re-run validation
5. If it's a new error class, add it to `KNOWN_ERRORS_AND_FIXES.md`

Never mark a task done until validation passes with no errors.

---

## Where the rules live

| What | Location |
|---|---|
| This file (all agents) | `AGENTS.md` ← you are here |
| Claude-specific overrides | `CLAUDE.md` |
| Cursor rules (auto-loaded) | `.cursor/rules/*.mdc` |
| VS Code Copilot | `.github/copilot-instructions.md` |
| Canonical rule source | `docs/agent/rules/` |
| Canonical skill source | `docs/agent/skills/` |
