# Analytics Use Case Library

> Start here (Business): `./docs/Business_Playbook.md`  
> One-pager: `./docs/Quickstart_1-Pager.md`

## Purpose
The Analytics Use Case Library is part of the company-wide Reporting Framework. It translates strategic, tactical, and operational information needs into standardized, reusable analytical use cases organized by functional clusters.

Each use case links business goals with data structures, KPIs, and actions, ensuring clarity, comparability, and governance across all analytics initiatives.

> Goal: Enable consistent, goal-driven, and AI-ready reporting instead of tool-driven dashboards.

---

## Objectives
- Establish a unified structure for documenting business analytics scenarios.
- Align reporting across all functional clusters to the Reporting Strategy.
- Enable a shared language between business, data, and analytics teams.
- Create a foundation for standardized KPIs, actions, and insights.
- Support Copilot readiness through structured metadata and traceability.

---

## Reporting Framework Integration
The Library operationalizes the Reporting Framework defined in `./docs/Reporting_Strategy.md`.

| Element | Role | Example |
|----------|------|---------|
| Reporting Strategy | Levels (Strategic, Tactical, Operational) and analytics maturity (Descriptive -> Prescriptive) | `./docs/Reporting_Strategy.md` |
| Cluster (Domain) | Groups related business topics | `./usecases/01_Commercial/` |
| Use Case | One analytical question with KPIs and actions | `./usecases/01_Commercial/COM-001_Sales_Performance/Business_Factsheet.md` |
| KPI Catalog & Action Codes | Shared semantics and operational levers | `./_includes/kpi_catalog/README.md`, `./_includes/ActionCodes.md` |

Each Use Case is classified by:
- reporting_level: Strategic / Tactical / Operational
- analytics_stage: Descriptive / Diagnostic / Predictive / Prescriptive
- domain: Cluster affiliation (e.g., Commercial, Operational Efficiency)

This structure ensures traceability from business goals -> KPIs -> data -> actions.

---

## Repository Structure
```
analytics-usecase-library/
  docs/
    Reporting_Strategy.md
    Methodology.md
    Instructions.md
  usecases/
    01_Commercial/
      COM-001_Sales_Performance/
        Business_Factsheet.md   # front-matter + business narrative
        Technical_Factsheet.md  # data contract, semantic model, KPIs
        FactSheet.md            # legacy stub pointing to the two files
        README.md
      COM-002_Gross_Margin_Analysis/
        Business_Factsheet.md
        Technical_Factsheet.md
        FactSheet.md
        README.md
      COM-003_Promotion_Effectiveness/
        Business_Factsheet.md
        Technical_Factsheet.md
        FactSheet.md
        README.md
  _includes/
    ActionCodes.md
    Glossary.md
    kpi_catalog/
      README.md
      SCHEMA.md
      KPI_Catalog_Growth.md
      KPI_Catalog_Profitability.md
      KPI_Catalog_Liquidity.md
      KPI_Catalog_Efficiency.md
      KPI_Catalog_CustomerValue.md
      KPI_Catalog_ESG.md
      KPI_Catalog_Governance.md
      KPI_Catalog_InnovationPeople.md
  schemas/
    TMDL_Official_Refs.md
    best_practices/
      bpa-rules-report.json
      bpa-rules-semanticmodel.json
  tools/
    alignment/
      build_alignment_map.ps1
    coverage/
      check_factsheet_vs_kpi.ps1
      validate_kpi_catalog.ps1
    run_all_checks.ps1
    generate/
      generate_tmdl_measures.ps1
```

Last updated: 27.11.2025

---

## How to run checks & regenerate measures

### 1. All quality checks

From the repo root:

```powershell
./tools/run_all_checks.ps1
```

This runs:
- `tools/coverage/validate_factsheets.ps1` - checks Business factsheet frontmatter/schema (via the FactSheet stub pointers).
- `tools/coverage/validate_kpi_catalog.ps1` - validates KPI catalog blocks.
- `tools/coverage/check_factsheet_vs_kpi.ps1` - verifies that all `required_kpi_ids` exist in the KPI catalogs.

Use this after edits to Use Cases or KPI catalogs.

### 2. Regenerate `_Measures.tmdl` for a Use Case

From the repo root:

```powershell
./tools/generate/generate_tmdl_measures.ps1 -UseCase COM-001
```

- Reads `required_kpi_ids` from `usecases/.../COM-001*/Business_Factsheet.md` (or follows the `FactSheet.md` pointer).
- Looks up KPI metadata in `_includes/kpi_catalog/*.md`.
- Writes/overwrites `dist/COM-001/.../_Measures.tmdl` and `measures_manifest.json`.

Omit `-UseCase` to regenerate measures for all Use Cases with `required_kpi_ids`.

