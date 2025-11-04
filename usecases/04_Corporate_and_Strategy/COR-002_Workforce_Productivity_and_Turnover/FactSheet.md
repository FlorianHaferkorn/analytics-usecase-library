---
id: "COR-002"
title: "Workforce Productivity & Turnover Analysis"
domain: "Corporate and Strategy"
owner: "Head of HR Controlling / People Analytics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Revenue per FTE", "Personnel Cost Ratio %", "Turnover Rate %"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "hr.personnel_cost_ratio.pct", "hr.turnover.pct"]
action_codes: ["C1", "SP1", "O2", "D1", "O3"]
expected_impact: "+5-10 % Revenue per FTE; -2-4 % Personnel Cost Ratio; +3-5 pp turnover improvement"
required_kpi_ids: [
  "hr.revenue_per_fte.amount",
  "hr.gm_per_fte.amount",
  "hr.personnel_cost_ratio.pct",
  "hr.turnover.pct",
  "hr.absenteeism.pct"
]
required_kpis:
  hr.revenue_per_fte.amount: "Revenue per FTE"
  hr.gm_per_fte.amount: "Gross Margin per FTE"
  hr.personnel_cost_ratio.pct: "Personnel Cost Ratio %"
  hr.turnover.pct: "Turnover Rate %"
  hr.absenteeism.pct: "Absenteeism %"

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Org.Region>Area>Store","Product.Category>Subcategory>SKU","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

data_requirements:
  facts:
    - name: fact_main
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"---

# Workforce Productivity & Turnover Analysis

## 1. Business Goal
Improve organizational efficiency and employee retention by tracking productivity, cost, and turnover trends â€” enabling data-driven workforce planning and early identification of risk areas.

## 3. Key Questions
- How has productivity evolved per department, region, or function?  
- What are the main drivers of workforce cost increases?  
- Which segments show high turnover or absenteeism risk?  
- What is the cost impact of employee churn?  
- How does engagement or tenure correlate with performance?

## 5. Required Attributes (Business-Level)
- Employee ID (anonymized or aggregated)  
- Org Unit, Department, Country  
- Hire Date, Leave Date, Status (Active/Exited)  
- FTE Factor, Contract Type (Full/Part-Time)  
- Net Sales Amount, Gross Margin Amount, Personnel Cost  
- Optional: Age Group, Tenure, Engagement Score, Job Level

## 7. Scope & Assumptions
- Productivity = output (Sales, Margin) / workforce input (FTEs, Cost).  
- Turnover = exits / average headcount over period.  
- Personnel Cost includes salaries, bonuses, social costs.  
- FTE values standardized to 1.0 for full-time equivalent.  
- All data aggregated and anonymized for compliance.

## 9. Edge Cases & QA Rules
- Headcount and FTE cannot be negative.  
- Turnover % capped at [0; 100].  
- Cross-check Revenue per FTE with Finance totals.  
- Referential integrity >= 99.9 % across Date/Org.  
- Privacy compliance per GDPR (no individual-level display).

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Identify and address high-turnover departments | C1 | Turnover -3-5 pp; retention improves |
| Optimize workforce mix (perm/temp) based on productivity | SP1 | Personnel Cost -2-4 % |
| Link bonus pools to productivity KPIs | O2 | Revenue per FTE improves; engagement improves |
| Launch engagement or wellbeing programs | D1 | Absenteeism reduces; retention improves |
| Automate HR analytics in S&OP and budgeting | O3 | Planning accuracy improves; latency reduces |

## 13. Related Processes
Workforce Planning -> Budgeting & Forecasting -> Talent Management -> Engagement & Wellbeing -> HR Analytics.

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_



