---
id: "COR-015"
title: "Forecast Reconciliation (Bottom-Up â†” Top-Down)"
domain: "Corporate and Strategy"
owner: "Head of Planning / FP&A"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Revenue Growth %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "fin.liquidity.working_capital"]
action_codes: ["SP1", "P2", "O2"]
expected_impact: "Automatically reconcile bottom-up and top-down forecasts to a single consensus forecast across Commercial, Operations and Finance, reducing bias and re-planning effort."
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
    "Forecast_Versions_Defined",
    "Consensus_Rules_Documented",
    "Plan_vs_Actual_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.net_sales.amount.forecast",
    "sales.forecast.mape_pct",
    "sales.forecast.bias_pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.amount.forecast: "Net Sales Amount (Forecast)"
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
    - name: fact_forecast
      grain: forecast_line
      primary_key: [ForecastLineID]
      required_columns:
        - { name: "Forecast Version", type: string, role: attribute }
        - { name: "Forecast Type", type: string, role: attribute } # BottomUp/TopDown/Consensus
        - { name: "Forecast Date", type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
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
    - { from: fact_forecast.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast."Forecast Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Forecast Reconciliation (Bottom-Up " Top-Down) - Business Factsheet

## 1. Summary
- **Business Goal:** Reduce forecast bias and re-planning effort by reconciling bottom-up and top-down forecasts into a single consensus forecast by org, product and period.

---
- **Target Audience:** Head of Planning / FP&A
- **Business Priority:** High
- **Expected Impact:** Automatically reconcile bottom-up and top-down forecasts to a single consensus forecast across Commercial, Operations and Finance, reducing bias and re-planning effort.

## 2. Core Questions
- Wie stark weichen Bottom-Up- und Top-Down-Forecasts aktuell voneinander ab " nach Org, Produkt und Zeitraum?
- Welche Kombination aus beiden liefert den geringsten Fehler im Vergleich zu tatschlichen Ergebnissen?
- Wie wirken sich unterschiedliche Reconciliation-Regeln (z.B. proportionale Anpassung, Priorisierung bestimmter Ebenen) auf MAPE und Bias aus?
- Wie verteilen wir den finalen Consensus Forecast zurck auf detaillierte Hierarchien (Org, Produkt, Kunde)?
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
- KPI cards for Net Sales Amount, Net Sales Amount (Forecast), Forecast Accuracy (MAPE %), Forecast Bias % with Plan/LY deltas.
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