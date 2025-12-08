---
id: "COM-008"
title: "Sales Forecast Accuracy"
domain: "Commercial"
owner: "Head of Sales Planning / Demand Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Working Capital %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "ops.working_capital.pct"]
action_codes: ["P2", "I1", "SP1"]
expected_impact: "+5â€“10 pp forecast accuracy; lower safety stocks and firefighting."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Forecast_vs_Actual_Aligned", "MAPE_InRange"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.amount.forecast",
  "sales.forecast.mape_pct",
  "sales.forecast.bias_pct"
]
required_kpis:
  sales.net_sales.amount: "Actual Net Sales Amount"
  sales.net_sales.amount.forecast: "Forecast Net Sales Amount"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
  sales.forecast.bias_pct: "Forecast Bias %"
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
        - { name: Channel, type: string, role: channel }
    - name: fact_forecast
      grain: sku_period_org
      primary_key: [ForecastID]
      required_columns:
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
        - { name: "Forecast Units Qty", type: decimal, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel", type: string, role: channel }
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
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Sales Forecast Accuracy - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and improve the accuracy and bias of sales forecasts by channel, region, and product hierarchy, in order to reduce firefighting, optimize inventory and capacity planning, and increase trust in the planning process.
- **Target Audience:** Head of Sales Planning / Demand Planning
- **Business Priority:** High
- **Expected Impact:** +5-10 pp forecast accuracy; lower safety stocks and firefighting.

## 2. Core Questions
- How accurate are our sales forecasts across regions, channels, and product hierarchies?
- Where do we systematically over- or under-forecast (bias) and why?
- Which combinations of product/channel/region show the highest error and volatility?
- How does forecast accuracy link to inventory days, service level, and working capital?

## 3. KPI Set (Business View)
| KPI                       | Definition                                              | Unit | Format   |
|---------------------------|---------------------------------------------------------|------|----------|
| Forecast Accuracy (MAPE)  | Mean absolute percentage error vs actual net sales     | %    | 1 decimal |
| Forecast Bias %           | (Forecast - Actual) / Actual                           | %    | 1 decimal |
| Actual Net Sales Amount   | Sum of actual net sales                                | EUR  |  #,0.00 |
| Forecast Net Sales Amount | Sum of forecasted net sales                            | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Exclude low-volume items below a minimum threshold when calculating MAPE.
- Validate that forecast and actuals share identical hierarchies and calendars.

## 5. Action Codes (Business Perspective)
| Action                                    | Code | Expected Effect                      |
|-------------------------------------------|------|--------------------------------------|
| Focus forecasting effort on volatile SKUs | P2   | MAPE improves on critical segments   |
| Adjust planning process where bias is high| SP1  | Lower bias and more stable volumes   |
| Align planning horizons and granularity   | I1   | Less re-planning and firefighting    |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Actual Net Sales Amount, Forecast Net Sales Amount, Forecast Accuracy (MAPE %), Forecast Bias % with Plan/LY deltas.
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
- Forecasts are frozen snapshots taken before the period starts (no rolling overrides).
- Actuals are net of returns and cancellations.
- MAPE and Bias are calculated only for periods with sufficient volume to avoid distortion.

## 8. Success Criteria
| Dimension       | Expected Impact              | Measurement     |
|-----------------|------------------------------|-----------------|
| Efficiency      | -10-20 % re-planning cycles | vs baseline     |
| Working Capital | -5-10 % inventory days      | vs prior year   |
| Service Level   | +1-2 pp service level       | vs prior year   |