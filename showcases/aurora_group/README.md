# Aurora Group Showcase

Purpose:
Demonstrate the ActionReady Analytics Framework end-to-end with a realistic synthetic company — and **validate** that use cases built from the framework enable the data-driven reporting the framework promises.

## Where is what (this repo)

| What | Location |
|------|----------|
| **Framework spec** (strategy, operating model, golden thread) | `framework/strategy_operating_model/` — entry: `framework/strategy_operating_model/README.md` |
| **Use case specs** (canonical factsheets) | `framework/usecases/core/` (e.g. `COM-001_Sales_Performance/` with Business_Factsheet.md, Technical_Factsheet.md) |
| **KPI catalog** (single source for measure definitions) | `framework/kpi_catalog/KPI_Catalog.md` |
| **Data contracts** (domains, sources, synthetic config) | `framework/data_contracts/` |
| **Page templates** (3–30–300 layouts, governance) | `framework/templates/page_templates/` |
| **Generated TMDL** (all measures) | `semantic_models/CoreActionReady.SemanticModel/definition/tables/_Measures.tmdl` — ONE file, displayFolders per use case. Optional per-use-case build cache: `implementations/microsoft_fabric_powerbi/dist/<UseCase>/` |
| **Aurora demo** (this showcase) | `showcases/aurora_group/` — company profile, data/gold, semantic model (PBIP), usecase pointers, reporting layouts |
| **Implementation guide** (Fabric/Power BI how-to) | `implementations/microsoft_fabric_powerbi/guide/` — entry: `fabric_powerbi.md` |
| **Validation tools** | Stage 1 (CI gate): `_internal/tools/run_stage1_checks.ps1`; Fabric checks: `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1` |

## What we validate with Aurora

**Question:** Can someone take a framework use case, use Aurora's data and semantic model, and produce reporting that delivers the promised KPIs and data-driven decisions?

Aurora is the **concrete proof** that the framework's chain (strategy → KPIs → use cases → semantic model → report) works: same specs, same gold data, same 3–30–300 patterns, and one place to verify that the "data-driven reporting" promise holds.

## Aurora validation checklist (gate: "framework delivers")

Use this to confirm the framework delivers data-driven reporting through Aurora:

1. **Stage 1 green** — From repo root: `.\_internal\tools\run_stage1_checks.ps1`. Fix any failures.
2. **Aurora data** — Gold data present under `showcases/aurora_group/data/gold/` (e.g. fact_sales, dim_*). Semantic model/dataset points to this path (or deployed equivalent).
3. **Open PBIP** — Open `showcases/aurora_group/semantic_models/CoreActionReady.pbip` in Power BI Desktop (or open the SemanticModel folder as dataset).
4. **Report loads** — CoreActionReady report opens; visuals use the semantic model; no missing measures or broken refs.
5. **COM-001 (and scope) represented** — At least one page reflects COM-001 KPIs (and ideally COM-002, COM-003, OPS-001, SCM-001, FIN-001) as per factsheets; measures align with KPI catalog.
6. **3–30–300 layout** — Overview / Insights / Explorer (or equivalent) follow `framework/templates/page_templates/` and `reporting/pbip_layouts.md`; no ad-hoc calculations.

When all steps pass, Aurora validates that the framework enables the promised data-driven reporting.

---

What's inside

```yaml
aurora_group/
  company/          # Profile, operating model, org/value chain
  data/             # Synthetic gold layer
    gold/           # Parquet output (dimensions, facts)
    scripts/        # Gold data generators (Python); run from repo root — see data/scripts/README.md
  usecases/         # Demo core use cases (links to canonical framework/usecases factsheets)
  reporting/        # PBIP layouts and screenshots (3–30–300)
  semantic_models/  # CoreActionReady.pbip — live PBIP with _Measures.tmdl (all measures, organized by displayFolder)
```

How to use

- Start with `company/Aurora_Group_Profile.md` and `company/Aurora_Operating_Model.md`.
- Sample data lives in `data/gold/` (Delta tables: `gold/facts/fact_sales`, `gold/dimensions/dim_*`). To (re)generate gold data, run the Python scripts in `data/scripts/` from repo root (see `data/scripts/README.md`). Data contracts and source definitions are in `framework/data_contracts/`; this showcase consumes gold-layer outputs.
- Open `semantic_models/CoreActionReady.pbip` in Power BI Desktop; all measures are in `_Measures.tmdl`, organized by displayFolder per use case.
- Implement pages following `framework/templates/page_templates/*` and `reporting/pbip_layouts.md`.
- Align use cases with the canonical factsheets in `framework/usecases/core/` (references to main library).

To reproduce

Run from **repo root**:

1. **Prerequisites (one-time):** `cd _internal\tools\validation` then `npm ci`.
2. **Stage 1 (CI gate):** `.\_internal\tools\run_stage1_checks.ps1` — tool-agnostic checks (docs, refs, KPI ↔ use case). Fix any failures before continuing.
3. **Generate TMDL measures** into the showcase semantic model:
   ```
   .\_internal\tools\generation\generate_tmdl_measures.ps1 -UseCase COM-001,COM-002,COM-003,COM-004,OPS-001,SCM-001,FIN-001 -UseAuroraShowcase -OverwriteExisting
   ```
   Output: **ONE** `_Measures.tmdl` file with all measures, organized by displayFolder (e.g. `displayFolder: "COM-001"`). For per-use-case dist output, omit `-UseAuroraShowcase`.
4. **Fabric/Power BI checks** (if you have generated TMDL): `.\implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1 -AuroraTablesDir "showcases/aurora_group/semantic_models/CoreActionReady.SemanticModel/definition/tables"`.
5. **Gold data for all PBIP tables** (optional if missing): `py showcases/aurora_group/data/scripts/generate_missing_gold_xd_finance.py` — creates dim_queue, dim_issue, fact_cases, fact_wfm, fact_ap, fact_ar, fact_cash, fact_cashflow so the semantic model loads without path errors.
6. **Point the Aurora semantic model/dataset** to `showcases/aurora_group/data/gold/` (or your deployed gold path).

Scope for the demo

- COM-001, COM-002, COM-003
- OPS-001
- SCM-001
- FIN-001
See `usecases/core/*.md` in this folder for demo-specific pointers to canonical factsheets, data, and layouts.

Relations

- WHY: mirrors Aurora strategy and org in `company/`.
- HOW: uses operating-model rules from `framework/strategy_operating_model/operating_model/semantic_layer.md` and `data_governance.md`.
- WITH WHAT: relies on Action Codes, KPI catalog, measure dictionary.
- PATTERNS: applies the 3–30–300 templates from `framework/templates/page_templates/`.
