# Agent Instructions — Analytics Use Case Library

## Golden Thread Principle

Use cases and reports **reference** governed definitions — they do not define KPI meaning or action logic.

| Source of Truth | Location |
|---|---|
| KPI definitions | `core/kpi_catalog/` |
| Action logic | `core/action_codes/` |
| Semantic model conventions | `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md` |
| Page templates | `core/templates/page_templates/` |
| Schema authority | `tooling/ai/schemas/` |

---

## Use Cases

- Preserve YAML frontmatter (`id`, `factsheet_type: business`) and required sections on Business Factsheets; preserve `UseCase_Bracket.yaml` structure per schema.
- Only reference KPIs that exist in `core/kpi_catalog/`; never redefine KPI meaning, targets, or lineage in factsheets or brackets.
- Business Factsheets are prose-only (Lean 2.0). All machine-readable config lives in `UseCase_Bracket.yaml` (orchestration, governance, value driver model, UX layout rules).
- When adding or changing action code references, update `orchestration.action_code_ids` in `UseCase_Bracket.yaml`.

---

## Framework (KPI Catalog, Action Codes, Templates)

- Respect KPI catalog schema — see `core/kpi_catalog/` and `core/templates/kpi_catalog_templates/`.
- Action code YAML must follow `core/templates/action_codes/` and `tooling/ai/schemas/action_code.schema.json`. All `kpi_id` values must exist in the KPI catalog.

---

## Scripts and CI

Run all scripts from the **repository root**.

| Task | Command |
|---|---|
| Stage 1 (required before commit) | `.\tooling\run_stage1_checks.ps1` |
| Fabric / Power BI validation | `.\products\fabric\powerbi\tooling\run_fabric_checks.ps1` |
| Full suite | `.\tooling\run_all_checks.ps1` |
| Sync evidence grain to factsheet | `.\tooling\maintenance\sync_evidence_grain_note_to_factsheet.ps1` |
| Full model generation | `.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1` |

---

## TMDL Conventions (Hard Rules — Enforced by PostToolUse Hook)

These rules are automatically checked after every Write/Edit on `.tmdl` files. Violations block the agent immediately.

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

### PostToolUse Hooks (Automatic)

Two hooks fire after every Write/Edit:
- **`validate-tmdl.sh`** — blocks on tab/`:=`/`description:` violations in `.tmdl` files
- **`validate-pbip-json.sh`** — blocks on JSON syntax errors in `.json`/`.pbir` files inside PBIP directories

Hooks are defined in `.claude/settings.json`. If a hook blocks you, fix the violation and retry — never bypass.

### Fabric CLI (`fab`)

Use `fab` for all Fabric data-plane operations (workspaces, models, reports, notebooks). Use `az` for Azure infrastructure (capacity, networking, RBAC).

**Quick start:**
```bash
fab auth login                        # Authenticate (opens browser)
fab auth status                       # Verify authentication
fab config set mode command_line      # Required for agent non-interactive mode
fab ls                                # List workspaces
fab ls "MyWorkspace.Workspace"        # List items in workspace
```

**Extract IDs for API calls:**
```bash
WS_ID=$(fab get "ws.Workspace" -q "id" | tr -d '"')
MODEL_ID=$(fab get "ws.Workspace/Model.SemanticModel" -q "id" | tr -d '"')
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

# Export model as PBIP
fab export "ws.Workspace/Model.SemanticModel" -o ./dist/Domain.SemanticModel

# Copy item across workspaces
fab cp "dev.Workspace/Item.Type" "prod.Workspace" -f

# Run notebook synchronously
fab job run "ws.Workspace/ETL.Notebook"
```

**Python utility scripts** (in `products/fabric/powerbi/tooling/scripts/`):

| Script | Purpose |
|---|---|
| `execute_dax.py` | Run DAX queries with JSON/CSV/ASCII output |
| `search_across_workspaces.py` | Cross-workspace item search via DataHub V2 API |
| `create_direct_lake_model.py` | Create Direct Lake semantic model from lakehouse tables |

Usage: `py -3 products/fabric/powerbi/tooling/scripts/execute_dax.py --help`

### PBIR Report Development

Reference docs for visual/report work are in `products/fabric/powerbi/docs/references/`:

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

## Learning Loop

When validation fails:
1. Read the error message carefully
2. Check `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` (symptom | cause | fix)
3. Fix the root cause
4. Re-run validation
5. If it's a new error class, add it to `KNOWN_ERRORS_AND_FIXES.md`

Never mark a task done until validation passes with no errors.
