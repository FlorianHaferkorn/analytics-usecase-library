---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
---

# Product Lifecycle Performance

## 1. Business Goal
Maximize category profitability and portfolio efficiency by tracking the performance of products throughout their lifecycle — from launch to maturity and phase-out — and by steering innovation, pricing, and discontinuation decisions based on data.

---

## 2. Business Context
Product portfolios naturally evolve: new launches must ramp up fast, mature items sustain volume, and tail products must be phased out efficiently.  
Without consistent lifecycle monitoring, assortments become bloated, marketing investments get misallocated, and product innovation ROI declines.  
This use case provides transparency across lifecycle stages to align product, sales, and marketing decisions with financial outcomes.

---

## 3. Key Questions
- How do products perform across lifecycle stages (Launch, Growth, Maturity, Decline)?  
- Which SKUs deliver the highest contribution and ROI?  
- When should a product be discontinued or relaunched?  
- How do pricing, margin, and promotion intensity evolve per phase?  
- What share of sales comes from new vs. existing products?  

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| New Product Share % | Sales of products <12 months / Total Sales | % | 1 decimal |
| Product Contribution Margin % | (NS - COGS - Promo Cost) / NS | % | 1 decimal |
| Lifecycle Age (months) | Months since first sale | Months | 0 decimals |
| Product ROI % | GM - Development & Marketing Cost / Cost | % | 1 decimal |
| Phase Distribution % | Share of portfolio in each lifecycle phase | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Product ID, Category, Subcategory, Launch Date  
- Net Sales Amount, COGS Amount, Promo Cost Amount  
- Units Qty, Margin Amount, Marketing Cost  
- Optional: Product Status (Active, Phase-Out), Country, Channel  

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU  
- Channel: Online / Offline / Partner  
- Org: Region > Country  
- Time: Year > Quarter > Month  
- Lifecycle: Launch / Growth / Maturity / Decline  

---

## 7. Scope & Assumptions
- Lifecycle classification based on sales age and trend:  
  - Launch = <6 months  
  - Growth = 6-18 months  
  - Maturity = 18-36 months  
  - Decline = >36 months or Δ% NS < -20 % YoY  
- Product ROI = (GM - DevCost - MktCost) / (DevCost + MktCost).  
- Currency = EUR; FX at transaction date.  
- Products inactive for >12 months automatically 'Phase-Out'.

---

## 8. Data Freshness & Cadence
- Refresh: monthly (5th business day post-close).  
- Latency <= 72h.  
- Historical depth = 36 months.  
- Data Owner: Product Analytics / Category Management.  

---

## 9. Edge Cases & QA Rules
- Product Launch Date must exist for lifecycle assignment.  
- Phase classification must cover 100 % of portfolio.  
- Missing cost components default to zero (flagged 'Incomplete').  
- Referential integrity >= 99.9 % across Date/Product/Org.  
- Phase transitions validated quarterly.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Product ID, Launch Date, Net Sales Amount, COGS Amount, Units Qty.  
- Optional: Promo Cost Amount, Marketing Cost, Margin Amount.  
- Extended: DevCost, Lifecycle Flag, Product Status, Channel.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Accelerate ramp-up of new launches via targeted promotions | D1 | Δ% NS +5-10 pp (Launch) |
| Reduce tail portfolio complexity (phase-out) | SP1 | COGS reduces; GM % improves |
| Adjust pricing of mature SKUs to protect margin | P2 | GM % +0.5-1 pp |
| Reinvest in top-growth categories and winning SKUs | SP2 | Δ% NS +2-4 pp |
| Optimize marketing mix across lifecycle stages | M3 | ROI +10-15 % |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Portfolio Efficiency | -10-20 % SKU count; +2 pp GM % | vs LY |
| Innovation ROI | +15-25 % ROI uplift | vs baseline |
| Revenue Growth | +3-5 % from new launches | 12M rolling |

---

## 13. Related Processes
Portfolio Management · Product Development · Category Planning · Pricing & Promotion Strategy.

---

## 14. Insights & Learnings
The majority of portfolios carry 30-40 % low-performing tail SKUs that erode margin.  
Lifecycle analytics allow dynamic reallocation of resources and faster decision-making in phase-out and pricing.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn](../03_Customer_and_Market/CST-001_Customer_Retention_and_Churn.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
  `[COR-004 Strategic KPI Dashboard](../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard.md)`  
- Related Documents:  
  [`KPI Catalog`](../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../_includes/ActionCodes.md) | [`Glossary`](../../_includes/Glossary.md)

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
