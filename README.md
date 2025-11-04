# Analytics Use Case Library

> Start here (Business): `./docs/Business_Playbook.md`  
> One‑pager: `./docs/Quickstart_1-Pager.md`

## Purpose
The Analytics Use Case Library is part of the company‑wide Reporting Framework. It translates strategic, tactical, and operational information needs into standardized, reusable analytical use cases organized by functional clusters.

Each use case links business goals with data structures, KPIs, and actions, ensuring clarity, comparability, and governance across all analytics initiatives.

> Goal: Enable consistent, goal‑driven, and AI‑ready reporting instead of tool‑driven dashboards.

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
| Reporting Strategy | Levels (Strategic, Tactical, Operational) and analytics maturity (Descriptive → Prescriptive) | `./docs/Reporting_Strategy.md` |
| Cluster (Domain) | Groups related business topics | `./usecases/01_Commercial/` |
| Use Case | One analytical question with KPIs and actions | `./usecases/01_Commercial/COM-001_Sales_Performance/FactSheet.md` |
| KPI Catalog & Action Codes | Shared semantics and operational levers | `./_includes/kpi_catalog/README.md`, `./_includes/ActionCodes.md` |

Each Use Case is classified by:
- reporting_level: Strategic / Tactical / Operational
- analytics_stage: Descriptive / Diagnostic / Predictive / Prescriptive
- domain: Cluster affiliation (e.g., Commercial, Operational Efficiency)

This structure ensures traceability from business goals → KPIs → data → actions.

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
        FactSheet.md
        README.md
      COM-002_Gross_Margin_Analysis/
        FactSheet.md
        README.md
      COM-003_Promotion_Effectiveness/
        FactSheet.md
        README.md
      COM-004_Price_Volume_Mix_Bridge/
        FactSheet.md
        README.md
    02_Operational_Efficiency/
      OPS-001_Cash_Conversion_Cycle/
        FactSheet.md
        README.md
      OPS-002_Inventory_Health/
        FactSheet.md
        README.md
      OPS-003_Purchase_Price_Variance/
        FactSheet.md
        README.md
      OPS-004_Replenishment_Optimization/
        FactSheet.md
        README.md
    03_Customer_and_Market/
      CST-001_Customer_Retention_and_Churn/
        FactSheet.md
        README.md
      CST-002_Product_Lifecycle_Performance/
        FactSheet.md
        README.md
    04_Corporate_and_Strategy/
      COR-001_Project_ROI_and_Benefit_Tracking/
        FactSheet.md
        README.md
      COR-002_Workforce_Productivity_and_Turnover/
        FactSheet.md
        README.md
      COR-003_ESG_and_Compliance_Monitoring/
        FactSheet.md
        README.md
      COR-004_Strategic_KPI_Dashboard/
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
```

Last updated: 04.11.2025
