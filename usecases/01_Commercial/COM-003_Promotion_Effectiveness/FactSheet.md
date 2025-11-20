---
id: "COM-003"
title: "Promotion Effectiveness (ROI & Uplift)"
domain: "Commercial"
owner: "Head of Marketing Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "Revenue Growth %"]
supports_strategic_kpi_ids: ["margin.gm.pct", "sales.revenue.growth_pct"]
action_codes: ["D1", "P2", "D2", "O2", "SP1"]
expected_impact: "+10-30 % ROI uplift; +0.5-1.0 pp GM %; +1-3 pp Δ% NS"

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
  "Product": "dim_product[ProductID]"
required_kpi_ids: [
  "sales.promo.roi.pct",
  "sales.promo.uplift_pct",
  "sales.promo.incremental.amount",
  "margin.promo.incremental.amount",
  "margin.promo.gm.pct",
  "sales.promo.cost.amount"
]
required_kpis:
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  sales.promo.incremental.amount: "Incremental Sales Amount"
  margin.promo.incremental.amount: "Incremental GM Amount"
  margin.promo.gm.pct: "GM % During Promo"
  sales.promo.cost.amount: "Promo Cost Amount"
---



# Use Case Fact Sheet

## 1. Business Goal
Quantify the financial return of promotions by measuring incremental revenue and margin uplift versus baseline performance, and enable optimized calendar planning, depth, and targeting.

---

## 2. Business Context
Promotions are among the largest controllable commercial investments but often lack consistent ROI evaluation.  
Different departments use separate definitions for uplift, base volume, and margin impact.  
This use case provides a standardized framework to assess promotional efficiency across channels and categories — linking revenue gain, margin impact, and investment cost in one model.

---

## 3. Key Questions
- Which promotions generated the highest incremental sales and margin uplift?  
- What is the ROI of promotion spend by product, channel, and region?  
- How do different promo mechanics (discount %, bundle, display) perform?  
- What share of promotion volume was truly incremental versus cannibalized?  
- Which calendar periods or channels deliver the best return on promo spend?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Promo ROI % | (Incremental GM - Promo Cost) / Promo Cost | % | 1 decimal |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % | 1 decimal |
| Incremental Sales Amount | Promo Sales - Baseline Sales | EUR | 0-2 decimals |
| Incremental GM Amount | Promo GM - Baseline GM | EUR | 0-2 decimals |
| GM % During Promo | (Promo NS - Promo COGS) / Promo NS | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (promotion period start/end)  
- Org (region, store)  
- Product (category, subcategory, SKU)  
- Channel (online/offline)  
- Net Sales Amount, Units Qty  
- Promo Flag, Promo ID, Promo Type, Promo Cost Amount  
- Optional: List Price Amount, COGS Amount, Baseline Volume  

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU  
- Org: Region > Area > Store  
- Channel: Online / Offline  
- Promo: Type > Subtype (Price Cut / Bundle / Display)  
- Time: Year > Month > Week

---

## 7. Scope & Assumptions
- Promo ROI = (Incremental GM - Promo Cost) / Promo Cost.  
- Baseline defined as rolling average of non-promo periods (e.g., -8 to -2 weeks).  
- Exclude overlapping promotions or multichannel effects for initial calculation.  
- Cost data (promo budget) from Marketing Spend Plan.  
- Reporting currency = EUR; FX at transaction date.

---

## 8. Data Freshness & Cadence
- Refresh frequency: weekly (Monday 07:00 CET)  
- Latency <= 3 days post-promo close  
- Backfill = 12 months history  
- Data Owner: Marketing Controlling

---

## 9. Edge Cases & QA Rules
- Exclude promos shorter than 2 days or with <5 transactions.  
- ROI capped between [-100%; +500%] to avoid outlier bias.  
- Ensure consistent baseline definition across products.  
- Validate incremental uplift against total market trends.  
- Referential integrity >= 99.9 % across Date/Org/Product/PromoID.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Promo Flag, Net Sales Amount, Promo Cost Amount  
- Optional: Baseline Volume, List Price, COGS Amount  
- Extended: Campaign ID, Promo Mechanic, Marketing Channel  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Optimize promotion calendar by ROI ranking | D1 | Δ% GM +0.5-1.0 pp; ROI +10-20 % |
| Reduce depth of low-return discounts | P2 | GM % +0.5 pp; NS stable |
| Focus investment on high-return mechanics | D2 | ROI +15-30 % |
| Improve baseline forecasting and promo tagging accuracy | O2 | Forecast bias reduces; reporting stability improves |
| Link trade marketing bonuses to measured ROI | SP1 | Long-term ROI alignment improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| ROI Improvement | +10-30 % ROI uplift | vs prior quarter |
| Profitability | +0.5-1.0 pp GM % | vs LY |
| Forecast Stability | -10 % forecast bias | Rolling 3M horizon |

---

## 13. Related Processes
Promotion Planning Â· Campaign Management Â· Marketing Budget Control Â· Sales Forecasting Â· Retail Execution.

---

## 14. Insights & Learnings
~30-40 % of promotions deliver marginal or negative ROI.  
Optimizing frequency and depth yields higher profitability than blanket discounting.  
Baseline model accuracy directly correlates with ROI reliability.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance](../COM-001_Sales_Performance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
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





