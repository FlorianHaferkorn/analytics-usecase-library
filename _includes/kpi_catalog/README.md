# KPI Catalog – Master Overview

---

## Purpose
The **KPI Catalog** defines all business and technical metrics used across the Analytics Use Case Library.  
Each dimension-specific catalog follows the **v2.0 YAML schema** (Strategic → Supporting/Diagnostic → Base Measures) and provides:  
- Unified KPI definitions for all business domains.  
- Complete lineage and metadata for Copilot and Fabric Semantic Link readiness.  
- Governance roles, QA rules, and review cycles for each metric.  

---

## Structure Overview

| File | Impact Dimension | Description |
|------|------------------|--------------|
| [KPI_Catalog_Growth.md](./KPI_Catalog_Growth.md) | **Growth** | Revenue, market, and volume expansion KPIs. |
| [KPI_Catalog_Profitability.md](./KPI_Catalog_Profitability.md) | **Profitability** | Margin, cost, and operational profit KPIs. |
| [KPI_Catalog_Liquidity.md](./KPI_Catalog_Liquidity.md) | **Liquidity** | Cash flow, working capital, and DSO/DPO metrics. |
| [KPI_Catalog_Efficiency.md](./KPI_Catalog_Efficiency.md) | **Efficiency** | Productivity, process, and cost-per-unit KPIs. |
| [KPI_Catalog_CustomerValue.md](./KPI_Catalog_CustomerValue.md) | **Customer Value** | Retention, NPS, CLV, and satisfaction KPIs. |
| [KPI_Catalog_ESG.md](./KPI_Catalog_ESG.md) | **ESG** | Environmental, social, and sustainability KPIs. |
| [KPI_Catalog_Governance.md](./KPI_Catalog_Governance.md) | **Governance** | Compliance, data quality, and audit KPIs. |
| [KPI_Catalog_InnovationPeople.md](./KPI_Catalog_InnovationPeople.md) | **Innovation & People** | Digital adoption, training, and engagement KPIs. |

---

## File Schema Summary

Each KPI entry in all catalogs follows the same **v2.0 YAML Schema**:

```yaml
- kpi_key: "Gross Margin %"
  kpi_type: "strategic | supporting | diagnostic | base"
  strategic_ref: "Gross Margin %"
  impact_dimension: "Profitability"
  domain_tag: ["Commercial"]
  use_case_ref: ["COM-002"]
  depends_on: ["Net Sales Amount","COGS Amount"]
  calc_type: "amount | ratio | rate | count"
  refresh: "daily | monthly | quarterly"
  status: "Active | Inactive"

  business:
    purpose: "Business meaning of the metric."
    definition: "Formula or business rule."
    grain_scope: "Granularity of data aggregation."
    unit_format: "% | € | pcs | days"
    interpretation: "Business interpretation."

  technical:
    dax_name: "Measure name in model"
    dax_expression: "DAX expression"
    lineage: ["Table.Column"]
    source_grain: "invoice_line | customer | product | employee"
    source_column_ref: ["fact_table.column"]
    source_system: "ERP | CRM | HR | Finance"
    verified: true

  governance:
    business_owner: "Business role accountable for KPI"
    data_owner: "Technical data owner"
    steward: "Operational KPI steward"
    review_cycle: "quarterly | monthly | annual"
    validation_process: "automated | manual | dual control"
    qa_rules:
      - "Rule or threshold 1"
      - "Rule or threshold 2"
    version: "v2.0"
    last_review: "12.10.2025"

  metadata_quality:
    completeness_score: 0.95
    lineage_verified: true
    copilot_ready: true
```

---

## Governance Model

| Role | Responsibility |
|------|----------------|
| **Business Owner** | Defines and validates KPI relevance and thresholds. |
| **Data Owner** | Ensures technical accuracy and lineage integrity. |
| **Steward** | Operates and monitors KPI quality and validation. |
| **Governance Board** | Approves KPI changes and additions via Pull Request. |

---

## Change Process

1. Create a new feature branch: `feature/KPI_<dimension>_<name>`  
2. Update or add KPI definitions in the corresponding catalog file.  
3. Validate YAML syntax and semantic lineage.  
4. Submit a Pull Request for review by:  
   - **1 Business Reviewer** (domain expert)  
   - **1 Data Reviewer** (model owner)  
5. Merge after Governance Board approval.

---

## Quality Standards

| Dimension | Completeness Target | Review Cycle | Owner |
|------------|--------------------|---------------|--------|
| Growth | ≥ 0.95 | Quarterly | Head of Sales |
| Profitability | ≥ 0.95 | Quarterly | Head of Controlling |
| Liquidity | ≥ 0.97 | Quarterly | Head of Treasury |
| Efficiency | ≥ 0.97 | Quarterly | Head of Operations |
| Customer Value | ≥ 0.97 | Quarterly | Head of Marketing |
| ESG | ≥ 0.96 | Semi-Annual | Head of Sustainability |
| Governance | ≥ 0.97 | Monthly | Chief Data Officer |
| Innovation & People | ≥ 0.97 | Quarterly | Head of HR |

---

## Automation & Copilot Readiness
- 100% of KPIs have structured YAML definitions.  
- All entries include data lineage (`lineage_verified: true`).  
- QA rules standardized for Data Quality validation pipelines.  
- Ready for integration with Fabric Semantic Link & Copilot authoring tools.  

---

_Last updated: 12.10.2025_
**Maintainers:** `analytics-core-team`  
**Contact:** `analytics-governance@company.com`  
