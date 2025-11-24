---
id: "COM-002"
title: "Gross Margin % vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi:
  - "Gross Margin %"
  - "Revenue Growth %"
supports_strategic_kpi_ids:
  - "margin.gm.pct"
  - "sales.revenue.growth_pct"
action_codes:
  - "P2"
  - "PC2"
  - "D1"
  - "M3"
  - "O2"
expected_impact: "+0.5-2.0 pp GM %; -1-3 % COGS; +1 pp Delta% Net Sales"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  - "Product.Category>Subcategory>SKU"
  - "Org.Region>Area>Store"
  - "Channel"
  - "Time.Year>Month>Week"
filters_default:
  - "Time: Last 12M"
  - "Org: All"
  - "Channel: All"
qa_asserts:
  - "RI_OK"
  - "GM_PositivePlan"
required_kpi_ids:
  - "margin.gm.pct"
  - "margin.gm.amount"
  - "margin.gm.delta_pct"
  - "cost.cogs.amount"
  - "sales.price.realization_pct"
  - "sales.net_sales.delta_pct.ly"
required_kpis:
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
  margin.gm.delta_pct: "Delta Gross Margin %"
  cost.cogs.amount: "COGS Amount"
  sales.price.realization_pct: "Price Realization %"
  sales.net_sales.delta_pct.ly: "Delta% Net Sales"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
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
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Price Realization %": "[Price Realization %]"
  "Date": "dim_date[Date]"
---

# Gross Margin % vs Plan & Last Year - Business Factsheet

## 1. Summary
- **Business Goal:** Protect and expand profitability by analyzing Gross Margin variance versus Plan and Last Year, identifying underlying price, mix, and cost effects, and translating findings into commercial and procurement actions.
- **Target Audience:** Head of Sales Controlling
- **Business Priority:** High
- **Expected Impact:** +0.5-2.0 pp GM %; -1-3 % COGS; +1 pp Delta% Net Sales

## 2. Core Questions
- What is the Delta and Delta% of Gross Margin vs Plan and Last Year?
- Which products, categories, and regions contribute most to variance?
- How much is driven by price, mix, or COGS changes?
- Are promotions profitable at the GM % level?
- Which suppliers or items drive margin erosion?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Gross Margin % | (Net Sales - COGS) / Net Sales | % | 1 decimal |
| Gross Margin Amount | Net Sales - COGS | EUR | 0-2 decimals |
| Delta Gross Margin % | GM % - Plan or LY GM % | % | 1 decimal |
| Price Realization % | Net Price / List Price | % | 1 decimal |
| COGS Amount | Direct product cost including logistics | EUR | 0-2 decimals |

## 4. Business Logic & Thresholds
- No negative GM % beyond -100% (data anomaly).
- Delta% GM calculated only where Plan GM % > 0.
- COGS must reconcile with financial postings (+/- 0.5 % tolerance).
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.
- Missing dimensions default to 'Unknown'.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Rebid or renegotiate supplier contracts | PC2 | COGS -1-3 %; GM % +1 pp |
| Tighten discount and rebate structure | P2 | GM % +0.5-1.0 pp |
| Review and optimize promo depth and ROI | D1 | GM % +0.5 pp; Delta% NS +1 pp |
| Channel/product mix steering toward high-margin lines | M3 | GM % +1 pp; stable NS |
| Improve cost-to-serve transparency (freight, packaging) | O2 | GM % +0.3-0.6 pp |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Gross Margin %, Gross Margin Amount, Delta Gross Margin %, COGS Amount, Price Realization % with Plan/LY deltas.
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
- Gross Margin calculated at invoice line level (Net Sales - COGS).
- Returns excluded from both Net Sales and COGS.
- Reporting currency = EUR; FX rate at transaction date.
- Plan data aligned with approved financial version.
- Cost allocations (e.g., freight, packaging) standardized per product.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Profitability | +0.5-2.0 pp GM % improvement | vs Plan |
| Cost Efficiency | -2-3 % COGS | vs LY |
| Promo ROI | +10-20 % uplift | per campaign |
