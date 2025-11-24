---
id: "COM-001"
title: "Sales Performance vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi:
  - "Revenue Growth %"
  - "Gross Margin %"
supports_strategic_kpi_ids:
  - "sales.revenue.growth_pct"
  - "margin.gm.pct"
action_codes:
  - "P2"
  - "D1"
  - "M3"
  - "SP1"
expected_impact: "+2-5 pp Delta% Net Sales; +0.5-1.5 pp Gross Margin %"
segments:
  - "Org.Region>Area>Store"
  - "Product.Category>Subcategory>SKU"
  - "Channel"
  - "Time.Year>Month>Week>Day"
filters_default:
  - "Time: Last 12M"
  - "Org: All"
  - "Channel: All"
page_template: "overview_drivers_details"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
qa_asserts:
  - "RI_OK"
  - "DeltaPct_OnlyWhenPlanPositive"
required_kpi_ids:
  - "sales.net_sales.amount"
  - "sales.net_sales.delta_amount.ly"
  - "sales.net_sales.delta_pct.ly"
  - "sales.price.realization_pct"
  - "sales.promo.uplift_pct"
  - "sales.pvm.price_effect.amount"
  - "sales.pvm.volume_effect.amount"
  - "sales.pvm.mix_effect.amount"
  - "margin.gm.pct"
  - "margin.gm.amount"
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.delta_amount.ly: "Delta Net Sales Amount"
  sales.net_sales.delta_pct.ly: "Delta% Net Sales"
  sales.price.realization_pct: "Price Realization %"
  sales.promo.uplift_pct: "Promo Uplift %"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
data_requirements:
  facts:
    - name: fact_sales
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
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Sales Performance vs Plan & Last Year - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure sustainable revenue growth by identifying and explaining deviations from Plan and Last Year early enough to steer pricing, promotions, and channel mix toward margin-accretive growth.
- **Target Audience:** Head of Sales
- **Business Priority:** High
- **Expected Impact:** +2-5 pp Delta% Net Sales; +0.5-1.5 pp Gross Margin %

## 2. Core Questions
- What is the Delta and Delta% of Net Sales vs Plan and Last Year?
- Which regions, products, or channels drive over-/underperformance?
- What are the main drivers: price, volume, mix, or promo depth?
- Which levers can recover revenue shortfalls or protect margins?
- How quickly can trends be detected and acted upon?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Net Sales Amount | Total invoiced sales excl. returns and taxes | EUR | 0-2 decimals |
| Delta Net Sales Amount | Net Sales - Plan (or LY) | EUR | 0-2 decimals |
| Delta% Net Sales | (Net Sales - Plan) / Plan | % | 1 decimal |
| Price Realization % | Net Price / List Price | % | 1 decimal |
| Promo Uplift % | (Promo Sales - Baseline) / Baseline | % | 1 decimal |

## 4. Business Logic & Thresholds
- No negative Net Sales Amount except for return flows
- Delta% Net Sales computed only when Plan > 0
- Price Realization % bounded [0%; 150%]
- Referential integrity >= 99.9 % across Date/Org/Product
- Missing dimensions default to 'Unknown' category

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Tighten Discounts - enforce corridor and reduce leakage | P2 | GM % +0.5-1.5 pp; NS stable |
| Optimize Promo Calendar - align depth and timing with demand | D1 | Delta% NS +1-3 pp; Forecast accuracy improves |
| Rebalance Channel/Product Mix toward high-margin items | M3 | GM % +1.0 pp; Delta% NS stable |
| Invest/Divest selectively across under/overperforming areas | SP1 | Profitability improves; capital efficiency improves |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Delta Net Sales Amount, Delta% Net Sales, Price Realization %, Promo Uplift % with Plan/LY deltas.
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
- Sales at invoice-line granularity, returns excluded from Net Sales
- Reporting currency EUR; FX at transaction date
- Plan version = current board-approved plan
- Actuals based on validated monthly close data
- Time zone = Europe/Berlin

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2-5 pp Delta% Net Sales | vs Plan |
| Profitability | +0.5-1.5 pp Gross Margin % | vs LY |
| Forecast Accuracy | +10-20 % lower MAPE | 4-8 week horizon |
