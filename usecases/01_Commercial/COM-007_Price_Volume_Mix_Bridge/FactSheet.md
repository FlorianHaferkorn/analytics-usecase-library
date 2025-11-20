---
id: "COM-007"
title: "Price–Volume–Mix Bridge (Portfolio & Strategic View)"
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
  sales.net_sales.delta_amount.ly: "Δ Net Sales Amount vs LY"
  margin.gm.delta_amount: "Δ Gross Margin Amount vs LY"
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

# Price–Volume–Mix Bridge (Portfolio & Strategic View)

## 1. Business Goal
Provide a strategic bridge that explains revenue and gross margin variance across the product and regional portfolio by decomposing into price, volume, and mix effects, enabling better planning and price governance.

---

## 2. Business Context
At group or business unit level, board members see only aggregated variances vs Plan or Last Year.  
Without a PVM bridge, it is hard to distinguish whether growth comes from volume, price increases, or mix shifts, and where margin dilution originates.  
This Use Case provides a standardized, portfolio-level PVM view that can be reused in steering decks and strategic reviews.

---

## 3. Key Questions
- How much of portfolio-level Δ Net Sales and Δ Gross Margin comes from price, volume, and mix?
- Which categories or regions generate favorable mix effects, and which ones dilute margin?
- Where do pricing decisions erode margin despite volume growth?
- How do structural mix shifts (channel, region) impact strategic KPIs?

---

## 4. Key KPIs
| KPI                   | Definition                                   | Unit | Format   |
|-----------------------|----------------------------------------------|------|----------|
| Δ Net Sales Amount    | Net Sales – Net Sales LY                     | EUR  | € #,0.00 |
| Δ Gross Margin Amount | Gross Margin – Gross Margin LY               | EUR  | € #,0.00 |
| Price Effect Amount   | (Actual Price – LY Price) × Actual Volume    | EUR  | € #,0.00 |
| Volume Effect Amount  | (Actual Volume – LY Volume) × LY Price       | EUR  | € #,0.00 |
| Mix Effect Amount     | Δ Total – (Price Effect + Volume Effect)     | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- Date (transaction date / period)
- Org (region, business unit)
- Product (category, subcategory)
- Channel (online/offline/wholesale)
- Net Sales Amount, Units Qty
- Optional: COGS Amount, List Price Amount

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory  
- Org: Region > Business Unit  
- Channel: Online / Offline / Wholesale  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- PVM is calculated vs Last Year or Plan with a consistent base definition.
- FX effects are handled separately or neutralized (constant currency).
- Promotions and one-offs are flagged to avoid misinterpreting structural price/mix effects.

---

## 8. Data Freshness & Cadence
- Data refresh: monthly after closing the period.
- Latency: ≤ 5 days after month-end close.
- Historical depth: at least 24 months.
- Data Owner: Sales Controlling / Finance.

---

## 9. Edge Cases & QA Rules
- Negative volumes and outlier prices are flagged.
- PVM reconciliation: Price + Volume + Mix ≈ Δ Total (tolerance < 0.5 %).

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Sales fact with Net Sales Amount, Units Qty, Date, Org, Product, Channel.
- Optional:
  - List Price, COGS, promo flags.

---

## 11. Typical Actions
| Action                                      | Code | Expected Effect             |
|---------------------------------------------|------|-----------------------------|
| Adjust pricing corridors for weak segments  | P2   | GM % improves, stable NS    |
| Focus growth on favorable mix categories    | M3   | GM % and NS both increase   |
| Re-balance regional/channel mix             | SP1  | More resilient profitability |

---

## 12. Expected Business Impact
| Dimension     | Expected Impact                  | Measurement |
|---------------|----------------------------------|-------------|
| Profitability | +0.5–1.5 pp Gross Margin %      | vs LY       |
| Transparency  | 100 % reconciled NS & GM variances | bridge vs P&L |

---

## 13. Related Processes
Planning & Forecasting → Monthly Performance Review → Pricing Governance.

---

## 14. Insights & Learnings
Typical findings include over-reliance on low-margin products or channels, and underutilized high-margin portfolios in specific regions.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance vs Plan & LY](../COM-001_Sales_Performance/FactSheet.md)`  
  `[COM-004 Price-Volume-Mix Bridge (Δ Net Sales & Δ Gross Margin)](../COM-004_Price_Volume_Mix_Bridge/FactSheet.md)`  
  `[COM-006 Customer Profitability](../COM-006_Customer_Profitability/FactSheet.md)`  

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

