---
id: "COM-002"
title: "Gross Margin % vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
supports_strategic_kpi: ["Gross Margin %", "Revenue Growth %"]
supports_strategic_kpi_ids: ["margin.gm.pct", "sales.revenue.growth_pct"]
action_codes: ["P2", "PC2", "D1", "M3", "O2"]
expected_impact: "+0.5-2.0 pp GM %; -1-3 % COGS; +1 pp Δ% Net Sales"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"`r`npage_template: "overview_drivers_details"`r`nsegments: [`r`n  "Product.Category>Subcategory>SKU",`r`n  "Org.Region>Area>Store",`r`n  "Channel",`r`n  "Time.Year>Month>Week"`r`n]`r`nfilters_default: [`r`n  "Time: Last 12M",`r`n  "Org: All",`r`n  "Channel: All"`r`n]`r`nrequired_kpi_ids: [
  "margin.gm.pct",
  "margin.gm.amount",
  "margin.gm.delta_pct",
  "cost.cogs.amount",
  "sales.price.realization_pct",
  "sales.net_sales.delta_pct.ly"
]
required_kpis:
  margin.gm.pct: "Gross Margin %"
  margin.gm.amount: "Gross Margin Amount"
  margin.gm.delta_pct: "Δ Gross Margin %"
  cost.cogs.amount: "COGS Amount"
  sales.price.realization_pct: "Price Realization %"
  sales.net_sales.delta_pct.ly: "Δ% Net Sales"

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
  "Date": "dim_date[Date]"---

# Use Case Fact Sheet

## 1. Business Goal
Protect and expand profitability by analyzing Gross Margin variance versus Plan and Last Year, identifying underlying price, mix, and cost effects, and translating findings into commercial and procurement actions.

---

## 2. Business Context
Gross Margin is the central performance indicator connecting commercial execution and cost management.  
Deviations often result from price pressure, promo depth, product mix shifts, or cost changes in sourcing and logistics.  
This use case quantifies and decomposes these effects, ensuring commercial, category, and procurement teams act on the same view of profitability drivers.

---

## 3. Key Questions
- What is the Δ and Δ% of Gross Margin vs Plan and Last Year?  
- Which products, categories, and regions contribute most to variance?  
- How much is driven by price, mix, or COGS changes?  
- Are promotions profitable at the GM % level?  
- Which suppliers or items drive margin erosion?  

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Gross Margin % | (Net Sales - COGS) / Net Sales | % | 1 decimal |
| Gross Margin Amount | Net Sales - COGS | EUR | 0-2 decimals |
| Δ Gross Margin % | GM % - Plan or LY GM % | % | 1 decimal |
| Price Realization % | Net Price / List Price | % | 1 decimal |
| COGS Amount | Direct product cost including logistics | EUR | 0-2 decimals |

---

## 5. Required Attributes (Business-Level)
- Date (transaction date)  
- Org (region, area, store)  
- Product (category, subcategory, SKU)  
- Net Sales Amount, COGS Amount  
- Optional: List Price, Promo Flag, Supplier, Plan GM %

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU  
- Org: Region > Area > Store  
- Supplier: Group > Vendor  
- Time: Year > Month > Week  
- Channel: Online / Offline

---

## 7. Scope & Assumptions
- Gross Margin calculated at invoice line level (Net Sales - COGS).  
- Returns excluded from both Net Sales and COGS.  
- Reporting currency = EUR; FX rate at transaction date.  
- Plan data aligned with approved financial version.  
- Cost allocations (e.g., freight, packaging) standardized per product.

---

## 8. Data Freshness & Cadence
- Refresh frequency: daily 06:00 CET  
- Latency <= 24h  
- Historical depth = 24 months  
- Data Owner: Sales Controlling / Procurement Analytics  

---

## 9. Edge Cases & QA Rules
- No negative GM % beyond -100% (data anomaly).  
- Δ% GM calculated only where Plan GM % > 0.  
- COGS must reconcile with financial postings (+/- 0.5 % tolerance).  
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.  
- Missing dimensions default to 'Unknown'.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Net Sales Amount, COGS Amount  
- Optional: List Price, Supplier, Plan GM %  
- Extended: FX Rate, Promo Flag, Logistic Cost Split  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Rebid or renegotiate supplier contracts | PC2 | COGS -1-3 %; GM % +1 pp |
| Tighten discount and rebate structure | P2 | GM % +0.5-1.0 pp |
| Review and optimize promo depth and ROI | D1 | GM % +0.5 pp; Δ% NS +1 pp |
| Channel/product mix steering toward high-margin lines | M3 | GM % +1 pp; stable NS |
| Improve cost-to-serve transparency (freight, packaging) | O2 | GM % +0.3-0.6 pp |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Profitability | +0.5-2.0 pp GM % improvement | vs Plan |
| Cost Efficiency | -2-3 % COGS | vs LY |
| Promo ROI | +10-20 % uplift | per campaign |

---

## 13. Related Processes
Pricing Governance -> Procurement Rebid Cycle -> Promotion Planning -> Financial Planning & Analysis.

---

## 14. Insights & Learnings
Price leakage through uncontrolled discounting is often a bigger GM driver than procurement costs.  
Mix effects (especially low-margin SKUs) explain up to 30 % of variance but are frequently overlooked in short-term reviews.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance](../COM-001_Sales_Performance/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-004 Price-Volume-Mix Bridge](../COM-004_Price_Volume_Mix_Bridge/FactSheet.md)`
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_











