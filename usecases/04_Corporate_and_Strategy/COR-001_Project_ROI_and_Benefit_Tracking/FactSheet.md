---
id: "COR-001"
title: "Project ROI & Benefit Tracking"
domain: "Corporate and Strategy"
owner: "Head of Strategy / PMO / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Project ROI %", "Benefit Realization %", "Operating Cost Ratio %"]
supports_strategic_kpi_ids: ["corp.project.roi.pct", "corp.benefit.realization.pct"]
action_codes: ["SP1", "SP2", "O2", "O3", "SP3"]
expected_impact: "+5-10 pp realized ROI; +15 % benefit realization; -10-20 % manual reporting effort"
required_kpi_ids: [
  "corp.project.roi.pct",
  "corp.benefit.realization.pct",
  "corp.budget.adherence.pct",
  "corp.schedule.adherence.pct",
  "corp.payback.months"
]
required_kpis:
  corp.project.roi.pct: "Project ROI %"
  corp.benefit.realization.pct: "Benefit Realization %"
  corp.budget.adherence.pct: "Budget Adherence %"
  corp.schedule.adherence.pct: "Schedule Adherence %"
  corp.payback.months: "Payback Period (Months)"

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

# Project ROI & Benefit Tracking

## 1. Business Goal
Ensure transparency on project performance by tracking realized financial and non-financial benefits versus investment cost â€” enabling data-driven portfolio steering, reprioritization, and early escalation.

## 3. Key Questions
- What is the realized ROI per project and portfolio segment?  
- Are projects delivering expected benefits on time and within budget?  
- Which initiatives drive the highest strategic and financial impact?  
- What portion of planned savings or revenue uplift is actually realized?  
- How do project delays correlate with ROI erosion?

## 5. Required Attributes (Business-Level)
- Project ID, Project Name, Portfolio, Strategic Pillar  
- Planned Cost, Actual Cost, Planned Benefits, Realized Benefits  
- Start Date, End Date, Stage (Initiation/Execution/Closed)  
- Optional: Sponsor, Project Type (CapEx/OpEx), Currency, Risk Level  

## 7. Scope & Assumptions
- Project ROI considers all CapEx + OpEx vs realized financial benefit.  
- Benefits captured when measurable in P&L (not forecast only).  
- Non-financial KPIs (e.g., CX, ESG) optionally tracked as qualitative.  
- Currency = EUR; FX rate at commitment date.  
- ROI target benchmark typically >= 15 %.  

## 9. Edge Cases & QA Rules
- Projects with ROI < -100 % flagged 'Loss-Making'.  
- Benefit > Planned Ã— 1.5 flagged for review (potential misallocation).  
- Project without closure date cannot report realized benefits.  
- Referential integrity >= 99.9 % across Project/Org/Time.  
- Status updates must align with PMO governance cadence.

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Reassess project scope or timeline if ROI < threshold | SP1 | ROI improves; delay reduces |
| Prioritize or divest projects based on realized ROI ranking | SP2 | Portfolio efficiency improves |
| Enforce benefit owner accountability | O2 | Benefit Realization % +10-15 pp |
| Introduce stage-gate reviews for high-risk projects | O3 | Risk exposure reduces; predictability improves |
| Link PMO bonus targets to benefit realization | SP3 | ROI target compliance improves |

## 13. Related Processes
Portfolio Management -> Strategic Planning -> Financial Forecasting -> PMO Governance -> CapEx Planning.

## 15. Cross-References
- Related Use Cases:  
  `[COR-002 Workforce Productivity & Turnover](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

_Last updated: 04.11.2025_



