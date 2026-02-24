# Aurora Group Showcase

Purpose:
Demonstrate the ActionReady Analytics Framework end-to-end with a realistic synthetic company — and **validate** that use cases built from the framework enable the data-driven reporting the framework promises.

## Where is what (this repo)

| What | Location |
|------|----------|
| **Framework spec** (strategy, operating model, golden thread) | `core/strategy_operating_model/` — entry: `core/strategy_operating_model/README.md` |
| **Use case specs** (canonical factsheets) | `core/usecases/core/` (e.g. `COM-001_Sales_Performance/` with Business_Factsheet.md, UseCase_Bracket.yaml) |
| **KPI catalog** (single source for measure definitions) | `core/kpi_catalog/KPI_Catalog.md` |
| **Data contracts** (domains, sources, synthetic config) | `core/data_contracts/` |
| **Page templates** (3–30–300 layouts, governance) | `core/templates/page_templates/` |
| **Generated TMDL** (per domain) | `semantic_models/<Domain>.SemanticModel/definition/tables/_Measures.tmdl` — one semantic model per domain (Commercial, Finance, Operations, etc.); displayFolders per use case. Optional per-use-case build cache: `products/fabric_powerbi/dist/<UseCase>/` |
| **Aurora demo** (this showcase) | `showcases/aurora_group/` — company profile, data/gold, semantic model (PBIP), usecase pointers, reporting layouts |
| **Implementation guide** (Fabric/Power BI how-to) | `products/fabric_powerbi/docs/` — entry: `fabric_powerbi.md` |
| **Validation tools** | Stage 1 (CI gate): `tooling/run_stage1_checks.ps1`; Fabric checks: `products/fabric_powerbi/tooling/run_fabric_checks.ps1` |

## What we validate with Aurora

**Question:** Can someone take a framework use case, use Aurora's data and semantic model, and produce reporting that delivers the promised KPIs and data-driven decisions?

Aurora is the **concrete proof** that the framework's chain (strategy → KPIs → use cases → semantic model → report) works: same specs, same gold data, same 3–30–300 patterns, and one place to verify that the "data-driven reporting" promise holds.

## Aurora validation checklist (gate: "framework delivers")

Use this to confirm the framework delivers data-driven reporting through Aurora:

1. **Stage 1 green** — From repo root: `.\tooling\run_stage1_checks.ps1`. Fix any failures.
2. **Aurora data** — Gold data present under `showcases/aurora_group/data/gold/` (e.g. fact_sales, dim_*). Semantic model/dataset points to this path (or deployed equivalent).
3. **Open PBIP** — Open a domain semantic model (e.g. `showcases/aurora_group/semantic_models/Commercial.SemanticModel`) or a generated report in Power BI Desktop. Reports reference their domain model via datasetReference.
4. **Report loads** — Report opens with scaffolded pages (e.g. COM-001 Overview/Detail) in PBIR format under `products/fabric_powerbi/dist/<UC>.Report/definition/`. Visuals use the domain semantic model; bind measures in Desktop as needed.
5. **COM-001 (and scope) represented** — At least one page reflects COM-001 KPIs (and ideally COM-002, COM-003, OPS-001, SCM-001, FIN-001) as per factsheets; measures align with KPI catalog.
6. **3–30–300 layout** — Overview / Insights / Explorer (or equivalent) follow `core/templates/page_templates/` and `reporting/pbip_layouts.md`; no ad-hoc calculations.

When all steps pass, Aurora validates that the framework enables the promised data-driven reporting.

---

What's inside

```yaml
aurora_group/
  company/          # Profile, operating model, org/value chain
  data/             # Synthetic gold layer
    gold/           # Parquet output (dimensions, facts)
    scripts/        # Gold data generators (Python); run from repo root — see data/scripts/README.md
  usecases/         # Demo core use cases (links to canonical core/usecases factsheets)
  reporting/        # PBIP layouts and screenshots (3–30–300)
  semantic_models/  # One folder per domain (Commercial.SemanticModel, Finance.SemanticModel, …); _Measures.tmdl per domain
```

How to use

- Start with `company/Aurora_Group_Profile.md` and `company/Aurora_Operating_Model.md`.
- Sample data lives in `data/gold/` (Delta tables: `gold/facts/fact_sales`, `gold/dimensions/dim_*`). To (re)generate gold data, run the Python scripts in `data/scripts/` from repo root (see `data/scripts/README.md`). Data contracts and source definitions are in `core/data_contracts/`; this showcase consumes gold-layer outputs.
- Open a domain semantic model (e.g. `semantic_models/Commercial.SemanticModel`) in Power BI Desktop; measures for that domain are in `_Measures.tmdl`, organized by displayFolder per use case.
- Implement pages following `core/templates/page_templates/*` and `reporting/pbip_layouts.md`.
- Align use cases with the canonical factsheets in `core/usecases/core/` (references to main library).

To reproduce

Run from **repo root**. Use-case scope has a **single source**: `core/usecases/core`. All use-case folders there with convention `ID_Title` and a valid `UseCase_Bracket.yaml` are discovered; scope is controlled by the orchestrate script.

1. **Prerequisites (one-time):** `cd tooling\validation` then `npm ci`.
2. **Stage 1 (CI gate):** `.\tooling\run_stage1_checks.ps1` — tool-agnostic checks (docs, refs, KPI ↔ use case). Fix any failures before continuing.
3. **Full pipeline (measures + model + reports):** Run the orchestrator with one of:
   - **All use cases:** `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -All`
   - **One domain:** `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -Domain Commercial`
   - **Single use case:** `.\tooling\powerbi_mcp\orchestrate_full_model.ps1 -UseCase COM-001`
   Output: **ONE** `_Measures.tmdl` in the showcase semantic model, plus reports under `products/fabric_powerbi/dist/<UC>.Report`. No hardcoded use-case list; scope comes from `-UseCase` / `-Domain` / `-All` and the contents of `core/usecases/core`.
   **Opening a generated report:** Open the report folder in Power BI Desktop (File → Open → `products/fabric_powerbi/dist/<UC>.Report`). The report’s dataset reference points to this showcase’s domain semantic model for that use case (e.g. COM-001 → Commercial.SemanticModel); see `products/fabric_powerbi/docs/fabric_powerbi.md` §3.4 for details.
4. **Fabric/Power BI checks** (if you have generated TMDL): `.\products\fabric_powerbi\tooling\run_fabric_checks.ps1 -AuroraTablesDir "showcases/aurora_group/semantic_models/Commercial.SemanticModel/definition/tables"` (or the domain model you built).
5. **Gold data for all PBIP tables** (optional if missing). Run in order:
   - (Optional) Framework gold for commercial + shared dimensions: `py core/data_contracts/sources/synthetic/generate_gold_layer_contract_v2.py` — produces dim_*, fact_sales under `showcases/aurora_group/data/gold/`.
   - Aurora gold for XD, Finance, Operations, Supply chain: `py showcases/aurora_group/data/scripts/generate_aurora_gold.py`.
   - (Optional) RLS user–org mapping: `py showcases/aurora_group/data/gold/generate_security_user_org.py`.
   See `data/scripts/README.md` for details.
6. **Point the Aurora semantic model/dataset** to `showcases/aurora_group/data/gold/` (or your deployed gold path).

Scope for the demo

Scope is determined by the orchestrate parameters (`-All`, `-Domain <name>`, or `-UseCase <id>`). The list of use cases is discovered from `core/usecases/core` (folders `ID_Title` with `UseCase_Bracket.yaml`). For a typical demo, use `-Domain Commercial` or `-All`. See `usecases/core/*.md` in this folder for demo-specific pointers to canonical factsheets, data, and layouts.

Relations

- WHY: mirrors Aurora strategy and org in `company/`.
- HOW: uses operating-model rules from `core/strategy_operating_model/operating_model/semantic_layer.md` and `data_governance.md`.
- WITH WHAT: relies on Action Codes, KPI catalog, measure dictionary.
- PATTERNS: applies the 3–30–300 templates from `core/templates/page_templates/`.
