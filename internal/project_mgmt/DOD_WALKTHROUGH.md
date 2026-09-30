# Framework v1.0 DoD Walkthrough

**Date:** 2026-04-20  
**Branch:** `claude/implement-execution-plan-bZbSq`  
**Reviewer:** CDAO sign-off required before merging to `main`

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python 3.10+ | `python3 --version` | Scripts, tests, generators |
| Node.js 20+ | `node --version` | Studio dev server |
| `fab` CLI | `fab --version` | Fabric data-plane operations |
| `az` CLI | `az --version` | Token acquisition for Fabric API |
| pyarrow | `pip show pyarrow` | Parquet read/write |

---

## Step 1: Strategy — Lean Core Catalog

The Golden 20 KPIs and Impactful 15 action codes are the authoritative spine.

```bash
# Confirm the files exist
cat core/kpi_catalog/golden_20.yaml          # 20 strategic KPIs
cat core/action_codes/impactful_15.yaml       # 15 action codes
```

**Expected:** Both files exist, all IDs reference entries in `core/kpi_catalog/KPI_Catalog.md` and `core/action_codes/`.

---

## Step 2: Forge — Compose → Generate

### 2a. Discover strategy anchors (Studio)

```bash
cd studio && npm run dev
```

Navigate to `http://localhost:3000/discover` and paste a sample executive memo. The AI extracts KPI anchors and populates the bracket draft.

### 2b. Blueprint the Golden Thread (Studio)

Navigate to `/blueprint`. Select any Aurora use case (e.g. `COM-001`). Verify the flow visualization shows:

```
Strategy Anchor → Strategic KPI → Influencing KPIs → Action Codes
```

### 2c. Compose a what-if scenario (Studio)

Navigate to `/compose`. Select `COM-001`. Adjust the formula slider — verify the impact output changes.

### 2d. Generate PBIP reports (IR path)

```bash
# From repo root — generates 15 reports from IR (no direct YAML parsing in Phase 2/5)
python3 products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py \
  --bracket core/usecases/core/COM-001_Commercial_NetSales/UseCase_Bracket.yaml \
  --output products/fabric/powerbi/dist/
```

Or via MCP:
```
studio mcp run_generator --use-case-id COM-001 --connector fabric
```

**Expected:** `products/fabric/powerbi/dist/Commercial.SemanticModel/` refreshed, zero errors.

---

## Step 3: Registry — Catalog → Drift → Approve

### 3a. Catalog health check (Studio)

Navigate to `/catalog`. Verify:
- KPI count ≥ 20 (Golden 20 present)
- Action count ≥ 15 (Impactful 15 present)
- Bracket count = 15 (all Aurora use cases)

### 3b. Drift scan (Studio + CI)

Navigate to `/drift`. Click **Scan Now**.

**Expected:** Zero `error`-severity rows for the Aurora use cases.

Command-line equivalent:
```bash
python3 tooling/validation/check_catalog_tmdl_drift.py 2>&1 | tail -5
```

### 3c. Action-outcome loop — XD-004 (Studio)

Navigate to `/catalog`, open bracket `XD-004`. Verify:
- `orchestration.strategic_kpi_id: KPI-GOV-001`
- All 15 Impactful action codes listed under `orchestration.action_code_ids`
- `readiness.data_availability: available`

### 3d. Governance approval (Studio)

Navigate to `/approvals`. Select `XD-004`. Click **Create snapshot**, then **Submit for review**.

**Expected:** Status transitions from `draft` → `review`.

---

## Step 4: Measure — Outcome Loop

### 4a. Verify fact_action_outcome Parquet

```bash
python3 -m pytest tooling/tests/test_action_outcomes.py -q
```

**Expected:** 26/26 tests pass.

Key assertions:
- 5 fiscal-year partitions exist (`Fiscal Year=2020` … `Fiscal Year=2024`)
- All 15 Impactful action codes present
- Every action code has at least one `achieved` or `partial` outcome row
- All 5 domain `_Measures.tmdl` files contain `measure 'Action Outcome Rate %'` in `"8_Action_Outcomes"` folder

### 4b. Run all validation tests

```bash
python3 -m pytest tooling/tests/ products/ -q
```

**Expected:** All tests pass, no errors.

### 4c. TMDL style and PBIR structure hooks

```bash
bash .claude/hooks/validate_tmdl_style.sh
bash .claude/hooks/validate_pbir_structure.sh
```

**Expected:** Both scripts exit 0.

---

## Step 5: Deploy — Fabric workspace

### 5a. Authenticate

```bash
fab auth login       # Opens browser
fab auth status      # Verify authenticated
```

### 5b. Deploy via MCP

```
# Via Studio MCP tool
studio mcp deploy_pbip --use-case-id COM-001 --workspace-name "Aurora Dev"
```

Or directly:
```bash
fab import "Aurora Dev.Workspace/Commercial.SemanticModel" \
  -i products/fabric/powerbi/dist/Commercial.SemanticModel -f
```

### 5c. Verify DAX

```
studio mcp execute_dax \
  --workspace-id "Aurora Dev" \
  --dataset-id "Commercial.SemanticModel" \
  --dax-query "EVALUATE ROW(\"OutcomeRate\", [Action Outcome Rate %])"
```

**Expected:** Returns a non-BLANK numeric value.

### 5d. Refresh dataset

```
studio mcp refresh_dataset --workspace-id <guid> --dataset-id <guid>
```

---

## Step 6: DoD Checklist

| # | Criterion | Status |
|---|---|---|
| 1 | `rm -rf dist/` + orchestrator regenerates 15 reports (no direct YAML parse) | ✅ |
| 2a | `validate_tmdl_style.sh` green | ✅ |
| 2b | `validate_pbir_structure.sh` green | ✅ |
| 2c | `validate_bindings.py --strict` 0 errors | ✅ |
| 2d | `check_catalog_tmdl_drift.py` 0 drift rows | ✅ |
| 3 | Every Impactful 15 action code has non-BLANK `[Action Outcome Rate %]` | ✅ |
| 4a | `core/kpi_catalog/golden_20.yaml` exists | ✅ |
| 4b | `core/action_codes/impactful_15.yaml` exists | ✅ |
| 5 | Studio has `(forge)/` and `(registry)/` route groups | ✅ |
| 5 | `studio/mcp-server.mjs` exposes `create_bracket`, `publish_draft`, `run_generator`, `validate_bindings`, `execute_dax`, `deploy_pbip`, `refresh_dataset`, `autofix_bindings` | ✅ |
| 6 | All `.claude/` hooks green throughout | ✅ |

**Release tag:** `v1.0.0` — "Lean Core & EcoPulse DoD"

---

## Rollback

Each weekly branch merges independently:
```bash
git revert <merge-sha> -m 1   # Never git reset --hard on main
```
