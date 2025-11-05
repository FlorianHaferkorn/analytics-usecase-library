---
id: "COR-004"
title: "Strategic KPI Dashboard (Enterprise Performance Overview)"
domain: "Corporate and Strategy"
owner: "Executive Board / Strategy Office"
impact: "Very High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Cash Conversion Cycle", "ESG-Aligned Revenue %", "Turnover %", "Project ROI %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days", "esg.aligned_revenue.pct", "hr.turnover.pct", "corp.project.roi.pct"]
action_codes: ["SP2", "O2", "SP1", "O3", "SP3"]
expected_impact: "Unified view of top KPIs; -50 % latency from data to decision; +100 % KPI-goal linkage"
required_kpi_ids: [
  "sales.net_sales.delta_pct.ly",
  "margin.gm.pct",
  "ops.working_capital.ccc.days",
  "hr.turnover.pct",
  "esg.aligned_revenue.pct",
  "corp.project.roi.pct"
]
required_kpis:
  sales.net_sales.delta_pct.ly: "Δ% Net Sales"
  margin.gm.pct: "Gross Margin %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
  hr.turnover.pct: "Turnover Rate %"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  corp.project.roi.pct: "Project ROI %"

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

# Strategic KPI Dashboard (Enterprise Performance Overview)

## 1. Business Goal
Provide a single, consolidated view of strategic KPIs across all business domains â€” enabling leadership to monitor execution of corporate strategy, track key objectives, and steer actions based on real-time insights.

## 3. Key Questions
- Are we on track to achieve corporate strategic and financial targets?  
- Which business domains drive value creation or risk?  
- How do operational, financial, and ESG metrics correlate?  
- Where are emerging risks or opportunities across the portfolio?  
- What trends require strategic intervention?

## 5. Required Attributes (Business-Level)
- Date (month-end or quarter-end)  
- Org (company, region, business unit)  
- Domain Source (Commercial, Operations, People, ESG, Strategy)  
- Actual, Plan, Forecast, and Target Values per KPI  
- Optional: Owner, Status (On Track / At Risk / Off Track), Commentary  

## 7. Scope & Assumptions
- KPIs sourced from validated domain models (semantic layer).  
- Actuals vs Plan harmonized per fiscal calendar (Mayâ€“April).  
- Each KPI has an assigned owner and update frequency.  
- Currency = EUR; consolidated at Group Level.  
- Refresh and validation aligned with monthly performance reviews.

## 9. Edge Cases & QA Rules
- KPI source must reference a validated Use Case ID.  
- Actual/Plan mismatch flagged automatically.  
- Missing commentary for 'Off Track' KPIs prohibited.  
- Referential integrity >= 99.9 % across Date/Org/KPI.  
- Audit trail required for changes in KPI definitions.

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Review and reprioritize initiatives in underperforming domains | SP2 | ROI improves; performance gap reduces |
| Launch strategic interventions for KPIs 'Off Track' | O2 | Execution speed improves; deviation reduces |
| Link KPI ownership to management scorecards | SP1 | Accountability improves; alignment improves |
| Integrate KPI narrative automation (AI-generated summaries) | O3 | Reporting latency reduces 70 % |
| Adjust strategic targets based on rolling forecasts | SP3 | Forecast bias reduces; agility improves |

## 13. Related Processes
Enterprise Performance Management -> Board Reporting -> Strategic Planning -> Financial Forecasting -> BI Governance.

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-002 Workforce Productivity & Turnover](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[COR-003 ESG & Compliance Monitoring](../COR-003_ESG_and_Compliance_Monitoring/FactSheet.md)`  
  `[COM-001 Sales Performance](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_




