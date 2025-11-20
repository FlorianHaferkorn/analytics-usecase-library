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
expected_impact: "+5–10 pp forecast accuracy; lower safety stocks and firefighting."
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

# Sales Forecast Accuracy

## 1. Business Goal
Measure and improve the accuracy and bias of sales forecasts by channel, region, and product hierarchy, in order to reduce firefighting, optimize inventory and capacity planning, and increase trust in the planning process.

---

## 2. Business Context
Sales and demand forecasts drive production planning, procurement, and financial projections.  
Poor forecast accuracy leads to excess inventory, stockouts, unstable service levels, and recurring re-planning cycles.  
This Use Case provides a standardized view on forecast vs actuals with transparent KPIs and drivers, enabling targeted improvements in process, tooling, and accountability.

---

## 3. Key Questions
- How accurate are our sales forecasts across regions, channels, and product hierarchies?
- Where do we systematically over- or under-forecast (bias) and why?
- Which combinations of product/channel/region show the highest error and volatility?
- How does forecast accuracy link to inventory days, service level, and working capital?

---

## 4. Key KPIs
| KPI                       | Definition                                              | Unit | Format   |
|---------------------------|---------------------------------------------------------|------|----------|
| Forecast Accuracy (MAPE)  | Mean absolute percentage error vs actual net sales     | %    | 1 decimal |
| Forecast Bias %           | (Forecast – Actual) / Actual                           | %    | 1 decimal |
| Actual Net Sales Amount   | Sum of actual net sales                                | EUR  | € #,0.00 |
| Forecast Net Sales Amount | Sum of forecasted net sales                            | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- Date (forecast period)
- Org (region, area, store)
- Product (category, subcategory, SKU)
- Channel (online/offline/wholesale)
- Actual Net Sales Amount
- Forecast Net Sales Amount / Units

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU  
- Org: Region > Area > Store  
- Channel: Online / Offline / Wholesale  
- Time: Year > Month > Week  

---

## 7. Scope & Assumptions
- Forecasts are frozen snapshots taken before the period starts (no rolling overrides).
- Actuals are net of returns and cancellations.
- MAPE and Bias are calculated only for periods with sufficient volume to avoid distortion.

---

## 8. Data Freshness & Cadence
- Forecasts: updated monthly or weekly depending on planning cycle.
- Actuals: daily or weekly, depending on sales posting.
- Data Owner: Sales Planning; Technical Owner: Commercial BI.

---

## 9. Edge Cases & QA Rules
- Exclude low-volume items below a minimum threshold when calculating MAPE.
- Validate that forecast and actuals share identical hierarchies and calendars.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Actual sales fact with amount and grain consistent with forecast.
  - Forecast fact with matching keys and periods.
- Optional:
  - Additional attributes (promo flag, price, customer segment) to explain error.

---

## 11. Typical Actions
| Action                                    | Code | Expected Effect                      |
|-------------------------------------------|------|--------------------------------------|
| Focus forecasting effort on volatile SKUs | P2   | MAPE improves on critical segments   |
| Adjust planning process where bias is high| SP1  | Lower bias and more stable volumes   |
| Align planning horizons and granularity   | I1   | Less re-planning and firefighting    |

---

## 12. Expected Business Impact
| Dimension       | Expected Impact              | Measurement     |
|-----------------|------------------------------|-----------------|
| Efficiency      | -10–20 % re-planning cycles | vs baseline     |
| Working Capital | -5–10 % inventory days      | vs prior year   |
| Service Level   | +1–2 pp service level       | vs prior year   |

---

## 13. Related Processes
Sales & Operations Planning (S&OP) → Demand Planning → Supply Planning → Execution Review.

---

## 14. Insights & Learnings
Typical findings include structural bias in certain regions or channels, and high volatility in specific product segments that require alternative planning approaches.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance vs Plan & LY](../COM-001_Sales_Performance/FactSheet.md)`  
  `[OPS-004 Replenishment Optimization & Service Level Management](../../02_Operational_Efficiency/OPS-004_Replenishment_Optimization/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

