---
id: "COM-001"
title: "Sales Performance vs Plan & Last Year"
domain: "Commercial"
owner: "Head of Sales"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
---

# Sales Performance vs Plan & Last Year

## 1. Business Goal
Ensure sustainable revenue growth by identifying and explaining deviations from Plan and Last Year early enough to steer pricing, promotions, and channel mix toward margin-accretive growth.

---

## 2. Business Context
Sales is the primary driver of both liquidity and profitability. Variances versus Plan or Last Year often arise from a combination of volume, price, mix, and promotion effects. Without a standardized variance logic, discussions focus on symptoms rather than causes.  
This use case provides a structured revenue bridge (Plan → Actual) and enables data-driven corrective actions across channels, products, and regions.

---

## 3. Key Questions
- What is the Δ and Δ% of Net Sales vs Plan and Last Year?  
- Which regions, products, or channels drive over-/underperformance?  
- What are the main drivers: price, volume, mix, or promo depth?  
- Which levers can recover revenue shortfalls or protect margins?  
- How quickly can trends be detected and acted upon?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Net Sales Amount | Total invoiced sales excl. returns and taxes | € | 0–2 decimals |
| Δ Net Sales Amount | Net Sales − Plan (or LY) | € | 0–2 decimals |
| Δ% Net Sales | (Net Sales − Plan) ÷ Plan | % | 1 decimal |
| Price Realization % | Net Price ÷ List Price | % | 1 decimal |
| Promo Uplift % | (Promo Sales − Baseline) ÷ Baseline | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (transaction date)  
- Org (region, area, store)  
- Product (category, subcategory, SKU)  
- Channel (online/offline/partner)  
- Net Sales Amount, Units Qty  
- Optional: Promotion Flag, List Price Amount, Plan Amount, LY Amount

---

## 6. Segmentation & Hierarchies
- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Channel: Online / Offline / Partner  
- Time: Year > Month > Week > Day

---

## 7. Scope & Assumptions
- Sales at invoice-line granularity, returns excluded from Net Sales  
- Reporting currency EUR; FX at transaction date  
- Plan version = current board-approved plan  
- Actuals based on validated monthly close data  
- Time zone = Europe/Berlin

---

## 8. Data Freshness & Cadence
- Refresh frequency: daily at 06:00 CET  
- Latency ≤ 24h  
- Backfill = 90 days  
- Data Owner: Commercial BI Team

---

## 9. Edge Cases & QA Rules
- No negative Net Sales Amount except for return flows  
- Δ% Net Sales computed only when Plan > 0  
- Price Realization % bounded [0%; 150%]  
- Referential integrity ≥ 99.9 % across Date/Org/Product  
- Missing dimensions default to “Unknown” category

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, Product, Net Sales Amount, Units Qty  
- Optional: Plan Amount, LY Amount  
- Extended: List Price, Promo Type, Margin Data  

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Tighten Discounts – enforce corridor and reduce leakage | P2 | GM % +0.5–1.5 pp; NS stable |
| Optimize Promo Calendar – align depth and timing with demand | D1 | Δ% NS +1–3 pp; Forecast accuracy ↑ |
| Rebalance Channel/Product Mix toward high-margin items | M3 | GM % +1.0 pp; Δ% NS stable |
| Invest/Divest selectively across under/overperforming areas | SP1 | Profitability ↑; capital efficiency ↑ |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2–5 pp Δ% Net Sales | vs Plan |
| Profitability | +0.5–1.5 pp Gross Margin % | vs LY |
| Forecast Accuracy | +10–20 % lower MAPE | 4–8 week horizon |

---

## 13. Related Processes
Sales Planning and Forecasting · Pricing Governance · Promotion Management · Channel Strategy · Account Planning.

---

## 14. Insights & Learnings
Price Realization usually contributes more to GM % variance than volume effects outside promotions.  
Promo intensity correlates inversely with overall margin quality — balanced governance yields optimal ROI.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
  `[COM-003 Promotion Effectiveness](../01_Commercial/COM-003_Promotion_Effectiveness.md)`  
  `[OPS-001 Cash Conversion Cycle](../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle.md)`
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
