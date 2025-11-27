---
id: "OPS-008"
title: "Unit Cost & COGS Drivers"
domain: "Operational Efficiency"
owner: "Head of Operations / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "COGS % of Sales"]
supports_strategic_kpi_ids: ["margin.gm.pct", "cost.cogs.amount"]
action_codes: ["PC2", "M1", "O2"]
expected_impact: "-2â€“4 % unit cost; +0.5â€“1.0 pp gross margin %."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Plant>Line",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All"
]
qa_asserts: ["RI_OK", "COGS_Positive", "UnitCost_Reconciles"]
required_kpi_ids: [
  "cost.cogs.amount",
  "ops.process.cost_per_unit.amount"
]
required_kpis:
  cost.cogs.amount: "COGS Amount"
  ops.process.cost_per_unit.amount: "Process Cost per Unit"
data_requirements:
  facts:
    - name: fact_production
      grain: product_line_day
      primary_key: [ProductionID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Direct Labor Cost Amount", type: decimal, role: amount }
        - { name: "Energy Cost Amount", type: decimal, role: amount }
        - { name: "Material Cost Amount", type: decimal, role: amount }
        - { name: "Other Production Cost Amount", type: decimal, role: amount }
    - name: fact_cogs
      grain: product_org_period
      primary_key: [CogsID]
      required_columns:
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Plant, type: string }
        - { name: Line, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_production.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_production.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_production.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Direct Labor Cost Amount": "fact_production[Direct Labor Cost Amount]"
  "Energy Cost Amount": "fact_production[Energy Cost Amount]"
  "Material Cost Amount": "fact_production[Material Cost Amount]"
  "Other Production Cost Amount": "fact_production[Other Production Cost Amount]"
  "COGS Amount": "fact_cogs[COGS Amount]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
---

# Unit Cost & COGS Drivers - Business Factsheet

## 1. Summary
- **Business Goal:** Understand and reduce unit cost (cost per produced/sold unit) and COGS by decomposing them into main cost drivers such as material, labor, and energy.
- **Target Audience:** Head of Operations / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** -2-4 % unit cost; +0.5-1.0 pp gross margin %.

## 2. Core Questions
- What is our unit cost per product, line, and plant, and how has it evolved?
- How much of unit cost is driven by material, labor, energy, or other components?
- Where are the largest improvement opportunities (e.g., energy efficiency, labor productivity)?

## 3. KPI Set (Business View)
| KPI                  | Definition                                        | Unit | Format   |
|----------------------|---------------------------------------------------|------|----------|
| COGS Amount          | Total cost of goods sold                          | EUR  |  #,0.00 |
| Process Cost per Unit| (Sum of production costs) / produced units        | EUR  |  #,0.000|
| Material Cost Share %| Material cost / total production cost             | %    | 1 decimal|
| Labor Cost Share %   | Direct labor cost / total production cost         | %    | 1 decimal|

## 4. Business Logic & Thresholds
- Periods with zero or very low production volume are flagged to avoid distorted unit costs.
- Cost component sums must reconcile with total cost within a small tolerance.

## 5. Action Codes (Business Perspective)
| Action                               | Code | Expected Effect             |
|--------------------------------------|------|-----------------------------|
| Optimize material yields             | PC2  | Lower material cost share   |
| Improve line efficiency and uptime   | M1   | Lower unit cost             |
| Adjust product/plant allocations     | O2   | Better utilization and cost |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for COGS Amount, Process Cost per Unit with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- COGS is aligned with production cost attribution for the analysis period.
- Depreciation and overhead allocation rules are documented and, if included, applied consistently.

## 8. Success Criteria
| Dimension   | Expected Impact   | Measurement  |
|-------------|-------------------|--------------|
| Profitability| +0.5-1.0 pp GM % | vs baseline  |
| Efficiency  | -2-4 % unit cost  | vs baseline  |