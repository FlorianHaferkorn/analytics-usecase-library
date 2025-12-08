---
id: "COR-012"
title: "Commercial & Supply Chain Reconciliation"
domain: "Corporate and Strategy"
owner: "COO / Head of Commercial & Supply Chain"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "CCC Days"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days"]
action_codes: ["P2", "W1", "D1", "SP1"]
expected_impact: "Avoid siloed commercial and operations decisions by reconciling promotions, pricing and forecast changes with stock, capacity and working capital."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts:
  [
    "Promo_Flag_Consistent",
    "Forecast_Version_Frozen",
    "Inventory_Valuation_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.promo.roi.pct",
    "sales.promo.uplift_pct",
    "margin.promo.incremental.amount",
    "ops.stockout.pct",
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.working_capital.ccc.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  margin.promo.incremental.amount: "Incremental GM Amount"
  ops.stockout.pct: "Stockout Rate %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Amount", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
    - name: fact_working_capital
      grain: org_period_wc
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "DSO Days", type: decimal, role: helper }
        - { name: "DPO Days", type: decimal, role: helper }
        - { name: "DIO Days", type: decimal, role: helper }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Promo ID": "fact_sales[Promo ID]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Commercial & Supply Chain Reconciliation - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure that commercial decisions (pricing, promotions, demand changes) are reconciled with supply chain realities (stock, capacity, working capital) to avoid stockouts, overstocks and margin dilution.

---
- **Target Audience:** COO / Head of Commercial & Supply Chain
- **Business Priority:** High
- **Expected Impact:** Avoid siloed commercial and operations decisions by reconciling promotions, pricing and forecast changes with stock, capacity and working capital.

## 2. Core Questions
- Welche Promotions und Preismanahmen haben zu Stockouts oder berbestnden gefhrt?
- Wo sehen wir hohe Promo-Uplifts bei gleichzeitig kritischen Service-Leveln?
- Welche Segmente oder Produkte treiben Working-Capital-Aufbau ohne entsprechenden Margenbeitrag?
- Gibt es systematische Forecast-Shifts in Commercial, die Supply Chain nicht rechtzeitig spiegeln kann?
- Wo mssen wir Prozesse oder Governance anpassen, um Commercial- und Supply-Chain-Plne besser abzustimmen?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Promo ROI %, Promo Uplift %, Incremental GM Amount, Stockout Rate % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a