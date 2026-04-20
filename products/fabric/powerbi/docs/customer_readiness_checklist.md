# Customer Readiness Checklist — Aurora Analytics Showcase

Use this checklist before any customer demo, pilot handover, or go-live. Work through each section in order. All **P0 blockers** must pass before proceeding.

---

## 1. Prerequisites

### 1.1 Local tooling

| Tool | Min version | Check |
|---|---|---|
| PowerShell | 7.4+ | `$PSVersionTable.PSVersion` |
| Python | 3.11+ | `python --version` |
| PyYAML | any | `pip show pyyaml` |
| jsonschema | any | `pip show jsonschema` |
| Git | 2.40+ | `git --version` |
| Power BI Desktop (optional) | Feb 2026+ | Open `dist/*.pbip` manually |
| `fab` CLI (optional, Fabric deploy) | 1.0+ | `fab --version` |
| Azure CLI (optional, az rest fallback) | 2.56+ | `az --version` |

### 1.2 Repository state

- [ ] On the correct branch and up to date (`git pull origin <branch>`)
- [ ] No uncommitted changes blocking validation (`git status`)
- [ ] `master_registry.json` present at `tooling/ontology/out/` (run Stage 1 if missing)

---

## 2. Stage 1 (required before any delivery)

Run from the repository root:

```powershell
.\tooling\run_stage1_checks.ps1
```

Expected: **all checks pass (exit 0)**.

Common blockers:

| Symptom | Cause | Fix |
|---|---|---|
| `master_registry.json not found` | Registry not built | Run `.\tooling\validation\check_registry_builder.ps1` |
| KPI ID not in catalog | Bracket references non-existent KPI | Add KPI to `core/kpi_catalog/` or fix `orchestration.strategic_kpi_id` |
| YAML schema violation | Malformed bracket | Validate against `tooling/ai/schemas/use_case_bracket.schema.json` |

---

## 3. Fabric / Power BI checks

```powershell
.\products\fabric\powerbi\tooling\run_fabric_checks.ps1
```

Runs:

| Check | Script | Purpose |
|---|---|---|
| TMDL syntax | `check_tmdl_syntax.ps1` | Tab indentation, `=` DAX, no `:=` |
| PBIP readiness | `check_tmdl_pbip_readiness.ps1` | Required TMDL fields for Desktop load |
| Diagram layout | `check_diagram_layout.ps1` | Spaghetti principle (model view positions) |
| Measures vs KPI | `check_measures_vs_kpi.ps1` | All measures have backing KPI catalog entries |
| TMDL vs dictionary | `check_tmdl_vs_measure_dictionary.ps1` | Measures match Measure_Dictionary |
| **Page structure** | `check_pbip_report_pages.ps1` | 2-page layout with correct visual slots |
| **Template compliance** | `check_page_template_compliance.py` | Bracket ↔ PBIP visual type alignment |

---

## 4. End-to-end pipeline smoke test

Generate all COM (Commercial) reports as a smoke test:

```powershell
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial -DryRun
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -Domain Commercial
```

Expected output:

```
  Step 1 Generate:       PASS
  Step 2 Desktop ready:  PASS
  Step 3 Page structure: PASS
  Step 4 Compliance:     PASS
  PIPELINE PASSED
```

For a complete build:

```powershell
.\products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1 -All -UseAuroraData
```

---

## 5. Visual spot-check (Power BI Desktop)

Open at least one report per domain in Power BI Desktop:

- [ ] `dist/COM-001_Sales_Performance.Report` (or the full `.pbip` file)
- [ ] No "Unable to connect" or "Expression.Error" dialogs on open
- [ ] Overview page loads with KPI cards, trend visual, date slicer
- [ ] Detail page loads with matrix table, slicer panel, smart narrative

> **Tip:** Use `Ctrl+Shift+D` (Desktop) to refresh the data connection and catch binding errors early.

---

## 6. Known blockers and fixes

See `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` for the full log. Common pre-demo issues:

| Symptom | Cause | Fix |
|---|---|---|
| `definition.pbir` missing `$schema` | Older generator output | Run `ensure_pbip_desktop_ready.ps1` |
| `definition.pbism` missing | SemanticModel not fully generated | Re-run Phase 3 in orchestrator or run `ensure_pbip_desktop_ready.ps1` |
| CardVisual shows "No data" | `_Measures.tmdl` not referencing the right table | Check `displayFolder` and table name in TMDL |
| ActionPanel slot missing | `action_panel: true` in bracket but Phase 4 skipped | Re-run `generate_aurora_pbip.ps1` for the affected use case |
| `check_page_template_compliance.py` fails `kpi_card` check | Scaffold generated with legacy `card` type | Re-generate scaffold; KPI_Cards must use `cardVisual` |

---

## 7. Deployment readiness (Fabric live demo)

Before deploying to Fabric workspace:

- [ ] `fab auth status` → authenticated
- [ ] Target workspace exists (`fab ls`)
- [ ] Semantic model imported: `fab import "ws.Workspace/Commercial.SemanticModel" -i ./dist/Commercial.SemanticModel -f`
- [ ] Report bound to correct semantic model (check `definition.pbir` `byPath`)
- [ ] Gateway / DirectLake connection configured (if non-local data)

---

## 8. Sign-off

| Owner | Check | Sign-off |
|---|---|---|
| BI Lead | Stage 1 clean | |
| BI Lead | Fabric checks clean | |
| BI Lead | Pipeline smoke test: Commercial | |
| Demo Owner | Desktop spot-check (2+ reports) | |
| Demo Owner | No blocking errors in Desktop | |
| Delivery Lead | Deployment to Fabric workspace (if live) | |
