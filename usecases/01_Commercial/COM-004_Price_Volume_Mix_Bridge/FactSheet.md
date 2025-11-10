---
id: "COM-004"
title: "Price-Volume-Mix Bridge (Δ Net Sales & Δ Gross Margin)"
domain: "Commercial"
owner: "Head of Sales Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["P2", "M3", "D1", "SP1", "O2"]
expected_impact: "100% reconciled variance; +0.5-1.5 pp GM %; +1-2 pp Δ% Net Sales"

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Product.Category>Subcategory>SKU","Org.Region>Area>Store","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

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
  "Product": "dim_product[ProductID]"---
required_kpi_ids: [
  "sales.net_sales.delta_amount.ly",
  "sales.pvm.price_effect.amount",
  "sales.pvm.volume_effect.amount",
  "sales.pvm.mix_effect.amount",
  "margin.gm.pct"
]
required_kpis:
  sales.net_sales.delta_amount.ly: "Δ Net Sales Amount"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"

# Price-Volume-Mix Bridge (Δ Net Sales & Δ Gross Margin)

## 1. Business Goal
Provide a unified analytical bridge that decomposes revenue and margin variance into price, volume, and mix components to explain why results deviate from Plan or Last Year — enabling targeted commercial and cost actions.

---

## 2. Business Context
Revenue and margin variances are often analyzed in isolation, obscuring their root causes.  
The Price-Volume-Mix (PVM) bridge unifies both perspectives by decomposing Δ Net Sales and Δ GM into quantifiable effects:
- Volume: Quantity change at constant price/mix  
- Price: Unit price change at constant volume/mix  
- Mix: Product/Channel/Region composition change  

This enables management to distinguish tactical from structural effects and to assign accountability.

---

## 3. Key Questions
- How much of Δ Net Sales and Δ Gross Margin comes from volume, price, or mix?  
- Which categories or regions drive mix gains or losses?  
- Are positive volume effects offset by unfavorable price or mix?  
- How do promotional periods distort PVM relationships?  
- What levers can improve the next planning cycle?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Δ Net Sales Amount | Net Sales - Plan/LY | EUR | 0-2 decimals |
| Δ Gross Margin Amount | (NS-COGS)_Actual - (NS-COGS)_Plan | EUR | 0-2 decimals |
| Price Effect Amount | (Actual Price - Plan Price) x Actual Qty | EUR | 0-2 decimals |
| Volume Effect Amount | (Actual Qty - Plan Qty) x Plan Price | EUR | 0-2 decimals |
| Mix Effect Amount | Δ Total - (Price + Volume) Effect | EUR | 0-2 decimals |

---

## 5. Required Attributes (Business-Level)
- Date (transaction date)  
- Org (region / store)  
- Product (category / SKU)  
- Channel (online / offline)  
- Net Sales Amount, Units Qty, List Price Amount  
- Optional: COGS Amount, Promo Flag, Plan / LY Values

---

## 6. Segmentation & Hierarchies
- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Channel: Online / Offline  
- Time: Year > Month > Week

---

## 7. Scope & Assumptions
- PVM decomposition calculated at invoice-line level.  
- Plan values fixed before execution; no rolling reforecast.  
- Reporting currency = EUR; FX at transaction date.  
- Negative volume excluded from mix effect.  
- Volume effect uses Plan Price; Price effect uses Actual Volume.

---

## 8. Data Freshness & Cadence
- Refresh: daily 06:00 CET  
- Latency <= 24 h  
- Backfill = 24 months  
- Data Owner: Sales Controlling / Finance BI

---

## 9. Edge Cases & QA Rules
- Price + Volume + Mix ~= Total Δ (variance < 0.5 %)  
- Plan Qty > 0 and Plan Price > 0 required.  
- Bound Δ% Price Effect [-30%; +50%].  
- Missing dimensions = 'Unknown'.  
- Referential integrity >= 99.9 %.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Units Qty, Net Sales Amount, List Price Amount  
- Optional: Plan/LY values, COGS Amount  
- Extended: Promo Flag, Discount Rate, Margin Data

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|----------------|
| Review price realization by segment and adjust corridors | P2 | GM % +0.5-1.0 pp |
| Optimize product mix toward high-margin SKUs | M3 | GM % +1 pp; Δ NS stable |
| Refocus promotions to offset unfavorable mix | D1 | Δ% NS +1-2 pp |
| Rebalance channel allocation based on unit economics | SP1 | Profit improves; margin stability improves |
| Integrate PVM logic into rolling forecast | O2 | Forecast variance -20 % |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|----------------|-------------|
| Revenue Insight | 100 % reconciled variance explanation | vs Plan |
| Profitability | +0.5-1.5 pp GM % | vs LY |
| Forecast Quality | -20 % MAPE | Rolling 3 M |

---

## 13. Related Processes
Sales & Margin Review Cycle -> Budget vs Actual Reporting -> Planning and Forecast Update -> Pricing Governance.

---

## 14. Insights & Learnings
Mix effects often explain > 30 % of variance but are under-discussed.  
Price pressure may increase volume but reduce overall margin efficiency.  
Automating PVM bridges creates a shared single source of truth for finance and sales.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance](../COM-001_Sales_Performance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|-------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_





