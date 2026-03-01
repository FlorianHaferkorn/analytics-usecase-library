# Implementation Guides

Platform-specific guides to implement the ActionReady framework. **Start here** for Fabric/Power BI.

## Purpose

Translate the **ActionReady Operating Model** (semantics, UX, governance, AI-readiness) into concrete, platform-specific implementation practices. Currently provided: **Microsoft Fabric / Power BI**.

## Data layers (Silver-first)

We **define Silver** via data contracts; we **deliver** Gold + Semantics. Start from Silver—do not start from Gold-only. See `core/strategy_operating_model/operating_model/data_layers_standard.md`.

---

## Scope

Included:

- Platform-specific mappings of:
  - Semantic Layer design  
  - Measure System enforcement  
  - Data Contract consumption  
  - Action Codes integration  
  - KPI governance  
  - Distribution & navigation patterns  
  - RLS/OLS patterns  
  - AI/Copilot-enablement  
- Recommended workspace / project structures  
- Best practices for pipelines, orchestration, and refresh

Not included:

- Raw ETL pipelines  
- Customer-specific provisioning processes  
- Tool-agnostic operating model principles (see `core/strategy_operating_model/operating_model/`)

---

## Framework and tooling entry points (this repo)

When implementing in Fabric/Power BI, use these in combination with this guide:

| Purpose | Location |
|--------|----------|
| Use case factsheets (business/technical) | `core/usecases/core/` (e.g. `COM-001_Sales_Performance/`) |
| KPI catalog (measure definitions, mapping) | `core/kpi_catalog/` |
| Stage 1 validation (docs, refs, structure) | `tooling/run_stage1_checks.ps1` |
| Full validation (Stage 1 + Fabric checks) | `tooling/run_all_checks.ps1` |
| Fabric-only checks (measures vs KPI, TMDL vs dictionary, DAX) | `products/fabric/powerbi/tooling/run_fabric_checks.ps1` |
| TMDL measure generation from KPI catalog | `tooling/generation/generate_tmdl_measures.ps1` |

Output for generated TMDL and reports: `products/fabric/powerbi/dist`. Pipeline: `products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1`. See **DEMO_AND_VERIFICATION.md** for run and verification steps.

---

## Structure

```yaml
products/fabric/powerbi/docs/
  fabric/powerbi.md                    # Implementation in Microsoft Fabric + Power BI ecosystem
  fabric_architecture_best_practices.md # Workspace strategy, CI/CD, Git, governance (framework-fit)
  tmdl_best_practices.md               # TMDL formatting and syntax for semantic models
  PBIP_REPORT_STRUCTURE.md             # Canonical PBIP report and semantic-model folder layout (Fabric)
  DEMO_AND_VERIFICATION.md             # Pipeline run, verification, pbi-tools, reproducibility
  reporting/                           # PBIP layouts, mockup validation, report documentation
  README.md                            # This file
```

### fabric/powerbi.md

Covers:

- PBIP structure  
- Dataset modeling & semantic alignment  
- Dataflows Gen2 / Lakehouse ingestion  
- Workspace structure (Dev/Test/Prod)  
- RLS/OLS patterns  
- Measure & DisplayFolder enforcement  
- App navigation & UX rules (3-30-300)
- Report themes & Power BI Theme Generator (standardized themes; tool lives in `products/fabric/powerbi/tooling/theme_generator/` and can be refined)

### Planned guides (not yet included)

- Databricks (Unity Catalog, Lakehouse)
- Snowflake + Tableau
- Looker

---

## Usage

### For Customers

- Understand how to realize the ActionReady Operating Model on their chosen platform  
- Validate readiness of their current architecture  
- Align internal IT & analytics teams on a common approach  

### For Delivery Teams

- Implement the same framework consistently across platforms  
- Use platform guides during solution design & review  
- Ensure all deliverables match the standards of the Operating Model  

### For Framework Evolution

- Add new platform guides as adoption expands  
- Keep platform patterns aligned with the core Operating Model  

---

## Relations

- **WHY ?** Derived from business strategy & domain definitions  
- **HOW ?** Platform-specific realization of the Operating Model  
- **WITH WHAT ?** Implements templates, Action Codes, KPIs, measure system  
- **TEMPLATES ?** Page templates and semantic templates map directly to platform structures

---

## Next step (single path)

1. **`fabric_architecture_best_practices.md`** — workspace strategy, CI/CD, Git, adoption path.
2. **`fabric/powerbi.md`** — operating model mapping, PBIP, measures, RLS, UX (Silver → Gold → Semantics).
3. **`tmdl_best_practices.md`** — TMDL syntax, formatting, DAX/measure conventions.
4. After changes: run **`run_fabric_checks.ps1`** from repo root (`products/fabric/powerbi/tooling/run_fabric_checks.ps1`).

---

**Location:**  
`products/fabric/powerbi/docs/README.md`
