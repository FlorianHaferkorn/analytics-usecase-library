---
id: "COM-003"
title: "Promotion Effectiveness (ROI & Uplift)"
domain: "Commercial"
owner: "Head of Marketing Controlling"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
---

# Promotion Effectiveness (ROI & Uplift)

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
| Promo ROI % | (Incremental GM − Promo Cost) ÷ Promo Cost | % | 1 decimal |
| Promo Uplift % | (Promo Sales − Baseline Sales) ÷ Baseline Sales | % | 1 decimal |
| Incremental Sales Amount | Promo Sales − Baseline Sales | € | 0–2 decimals |
| Incremental GM Amount | (Promo GM − Baseline GM) | € | 0–2 decimals |
| GM % During Promo | (Promo NS − Promo COGS) ÷ Promo NS | % | 1 decimal |

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
- Promo ROI = (Incremental GM − Promo Cost) ÷ Promo Cost.  
- Baseline defined as rolling average of non-promo periods (e.g., −8 to −2 weeks).  
- Exclude overlapping promotions or multichannel effects for initial calculation.  
- Cost data (promo budget) from Marketing Spend Plan.  
- Reporting currency = EUR; FX at transaction date.

---

## 8. Data Freshness & Cadence
- Refresh frequency: weekly (Monday 07:00 CET)  
- Latency ≤ 3 days post-promo close  
- Backfill = 12 months history  
- Data Owner: Marketing Controlling

---

## 9. Edge Cases & QA Rules
- Exclude promos shorter than 2 days or with <5 transactions.  
- ROI capped between [−100%; +500%] to avoid outlier bias.  
- Ensure consistent baseline definition across products.  
- Validate incremental uplift against total market trends.  
- Referential integrity ≥ 99.9 % across Date/Org/Product/PromoID.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Promo Flag, Net Sales Amount, Promo Cost Amount  
- Optional: Baseline Volume, List Price, COGS Amount  
- Extended: Campaign ID, Promo Mechanic, Marketing Channel  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Optimize promotion calendar by ROI ranking | D1 | Δ% GM +0.5–1.0 pp; ROI +10–20 % |
| Reduce depth of low-return discounts | P2 | GM % +0.5 pp; NS stable |
| Focus investment on high-return mechanics | D2 | ROI +15–30 % |
| Improve baseline forecasting and promo tagging accuracy | O2 | Forecast bias ↓; reporting stability ↑ |
| Link trade marketing bonuses to measured ROI | SP1 | Long-term ROI alignment ↑ |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| ROI Improvement | +10–30 % ROI uplift | vs prior quarter |
| Profitability | +0.5–1.0 pp GM % | vs LY |
| Forecast Stability | −10 % forecast bias | Rolling 3M horizon |

---

## 13. Related Processes
Promotion Planning · Campaign Management · Marketing Budget Control · Sales Forecasting · Retail Execution.

---

## 14. Insights & Learnings
~30–40 % of promotions deliver marginal or negative ROI.  
Optimizing frequency and depth yields higher profitability than blanket discounting.  
Baseline model accuracy directly correlates with ROI reliability.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-001 Sales Performance](../01_Commercial/COM-001_Sales_Performance.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
  `[COM-004 Price-Volume-Mix Bridge](../01_Commercial/COM-004_Price_Volume_Mix_Bridge.md)`
- Related Documents:  
  [`KPI Catalog`](../_includes/KPI_Catalog.md) · [`Action Codes`](../_includes/ActionCodes.md) · [`Glossary`](../_includes/Glossary.md)

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

_Last updated: 07.10.2025_
