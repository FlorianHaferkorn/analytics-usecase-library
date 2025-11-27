---
id: "COM-007"
title: "Priceâ€“Volumeâ€“Mix Bridge (Portfolio & Strategic View)"
domain: "Commercial"
owner: "Head of Sales / Head of Finance"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["P2", "M3", "SP1"]
expected_impact: "Transparent decomposition of revenue and margin variances at portfolio level; better planning quality and price discipline."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "Product.Category>Subcategory",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "PVM_Reconciles", "Price_Mix_Consistent"]
required_kpi_ids: [
  "sales.net_sales.delta_amount.ly",
  "margin.gm.delta_amount",
  "sales.pvm.price_effect.amount",
  "sales.pvm.volume_effect.amount",
  "sales.pvm.mix_effect.amount",
  "margin.gm.pct"
]
required_kpis:
  sales.net_sales.delta_amount.ly: "Î” Net Sales Amount vs LY"
  margin.gm.delta_amount: "Î” Gross Margin Amount vs LY"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"
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
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Price-Volume-Mix Bridge (Portfolio & Strategic View) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a strategic bridge that explains revenue and gross margin variance across the product and regional portfolio by decomposing into price, volume, and mix effects, enabling better planning and price governance.
- **Target Audience:** Head of Sales / Head of Finance
- **Business Priority:** High
- **Expected Impact:** Transparent decomposition of revenue and margin variances at portfolio level; better planning quality and price discipline.

## 2. Core Questions
- How much of portfolio-level Delta Net Sales and Delta Gross Margin comes from price, volume, and mix?
- Which categories or regions generate favorable mix effects, and which ones dilute margin?
- Where do pricing decisions erode margin despite volume growth?
- How do structural mix shifts (channel, region) impact strategic KPIs?

## 3. KPI Set (Business View)
| KPI                   | Definition                                   | Unit | Format   |
|-----------------------|----------------------------------------------|------|----------|
| Delta Net Sales Amount    | Net Sales - Net Sales LY                     | EUR  |  #,0.00 |
| Delta Gross Margin Amount | Gross Margin - Gross Margin LY               | EUR  |  #,0.00 |
| Price Effect Amount   | (Actual Price - LY Price)  Actual Volume    | EUR  |  #,0.00 |
| Volume Effect Amount  | (Actual Volume - LY Volume)  LY Price       | EUR  |  #,0.00 |
| Mix Effect Amount     | Delta Total - (Price Effect + Volume Effect)     | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Negative volumes and outlier prices are flagged.
- PVM reconciliation: Price + Volume + Mix  Delta Total (tolerance < 0.5 %).

## 5. Action Codes (Business Perspective)
| Action                                      | Code | Expected Effect             |
|---------------------------------------------|------|-----------------------------|
| Adjust pricing corridors for weak segments  | P2   | GM % improves, stable NS    |
| Focus growth on favorable mix categories    | M3   | GM % and NS both increase   |
| Re-balance regional/channel mix             | SP1  | More resilient profitability |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Delta Net Sales Amount vs LY, Delta Gross Margin Amount vs LY, Price Effect Amount, Volume Effect Amount, Mix Effect Amount with Plan/LY deltas.
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
- PVM is calculated vs Last Year or Plan with a consistent base definition.
- FX effects are handled separately or neutralized (constant currency).
- Promotions and one-offs are flagged to avoid misinterpreting structural price/mix effects.

## 8. Success Criteria
| Dimension     | Expected Impact                  | Measurement |
|---------------|----------------------------------|-------------|
| Profitability | +0.5-1.5 pp Gross Margin %      | vs LY       |
| Transparency  | 100 % reconciled NS & GM variances | bridge vs P&L |