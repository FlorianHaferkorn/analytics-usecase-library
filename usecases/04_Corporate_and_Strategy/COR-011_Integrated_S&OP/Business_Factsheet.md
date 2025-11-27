---
id: "COR-011"
title: "Integrated Sales & Operations Planning (S&OP)"
domain: "Corporate and Strategy"
owner: "COO / Head of S&OP"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi:
  [
    "Revenue Growth %",
    "Gross Margin %",
    "Working Capital %",
    "CCC Days",
  ]
supports_strategic_kpi_ids:
  [
    "sales.revenue.growth_pct",
    "margin.gm.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
  ]
action_codes: ["SP1", "P2", "W1", "O2"]
expected_impact: "Align demand, supply and financial plans into one consensus plan; reduce forecast error, inventory and stockouts while protecting margin."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Next 12M", "Org: All"]
qa_asserts:
  [
    "Forecast_Version_Frozen",
    "Supply_Capacity_Complete",
    "Plan_vs_Actual_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.net_sales.amount.forecast",
    "sales.forecast.mape_pct",
    "sales.forecast.bias_pct",
    "ops.capacity.utilization.pct",
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.stockout.pct",
    "fin.liquidity.working_capital",
    "ops.working_capital.ccc.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.amount.forecast: "Net Sales Amount (Forecast)"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
  sales.forecast.bias_pct: "Forecast Bias %"
  ops.capacity.utilization.pct: "Capacity Utilization %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.stockout.pct: "Stockout Rate %"
  fin.liquidity.working_capital: "Working Capital %"
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
    - name: fact_forecast
      grain: forecast_line
      primary_key: [ForecastLineID]
      required_columns:
        - { name: "Forecast Version", type: string, role: attribute }
        - { name: "Forecast Date", type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
        - { name: "Forecast Units Qty", type: decimal, role: quantity }
    - name: fact_capacity
      grain: org_resource_period
      primary_key: [OrgID, ResourceID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ResourceID, type: string, role: attribute }
        - { name: "Available Hours", type: decimal, role: amount }
        - { name: "Planned Load Hours", type: decimal, role: amount }
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
    - {
        from: fact_sales.Date,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_sales.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_forecast."Forecast Date",
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_capacity.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_capacity.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_inventory.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.OrgID,
        to: dim_org.OrgID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.ProductID,
        to: dim_product.ProductID,
        cardinality: many-to-one,
        direction: single,
      }
    - {
        from: fact_service_level.Period,
        to: dim_date.Date,
        cardinality: many-to-one,
        direction: single,
      }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Available Capacity Hours": "fact_capacity[Available Hours]"
  "Planned Load Hours": "fact_capacity[Planned Load Hours]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Integrated Sales & Operations Planning (S&OP) - Business Factsheet

## 1. Summary
- **Business Goal:** Create a single, integrated Sales & Operations Plan that aligns demand, supply and financials, reducing forecast error, inventory and stockouts while protecting gross margin and cash.

---
- **Target Audience:** COO / Head of S&OP
- **Business Priority:** Very High
- **Expected Impact:** Align demand, supply and financial plans into one consensus plan; reduce forecast error, inventory and stockouts while protecting margin.

## 2. Core Questions
- How does the demand forecast compare to recent actuals by region, channel and product family?
- Where do we see structural over- or under-forecasting (bias) by planner, segment or horizon?
- Do we have sufficient capacity to serve the planned demand and promotions without creating bottlenecks?
- Sind Inventory Targets (Safety Stock, DIO) konsistent mit Service-Level und CCC-Zielen?
- Wie stark weichen Ist-Produktion, Auslieferung und Umsatz vom S&OP-Consensus-Plan ab?
- Welche S&OP-Entscheidungen haben den grten Impact auf GM % und Working Capital?
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
- KPI cards for Net Sales Amount, Net Sales Amount (Forecast), Forecast Accuracy (MAPE %), Forecast Bias %, Capacity Utilization % with Plan/LY deltas.
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