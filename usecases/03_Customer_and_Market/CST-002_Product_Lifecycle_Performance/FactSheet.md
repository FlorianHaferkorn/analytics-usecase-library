---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: [
  "prod.lifecycle.new_share.pct",
  "prod.contribution_margin.pct",
  "prod.lifecycle.age.months",
  "prod.roi.pct",
  "prod.lifecycle.phase_distribution.pct"
]
required_kpis:
  prod.lifecycle.new_share.pct: "New Product Share %"
  prod.contribution_margin.pct: "Product Contribution Margin %"
  prod.lifecycle.age.months: "Lifecycle Age (months)"
  prod.roi.pct: "Product ROI %"
  prod.lifecycle.phase_distribution.pct: "Phase Distribution %"
---

# Product Lifecycle Performance

## 1. Business Goal
Maximize category profitability and portfolio efficiency by tracking the performance of products throughout their lifecycle — from launch to maturity and phase-out — and by steering innovation, pricing, and discontinuation decisions based on data.

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

## 3. Key Questions
- How do products perform across lifecycle stages (Launch, Growth, Maturity, Decline)?  
- Which SKUs deliver the highest contribution and ROI?  
- When should a product be discontinued or relaunched?  
- How do pricing, margin, and promotion intensity evolve per phase?  
- What share of sales comes from new vs. existing products?  

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

## 5. Required Attributes (Business-Level)
- Product ID, Category, Subcategory, Launch Date  
- Net Sales Amount, COGS Amount, Promo Cost Amount  
- Units Qty, Margin Amount, Marketing Cost  
- Optional: Product Status (Active, Phase-Out), Country, Channel  

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
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
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

## 9. Edge Cases & QA Rules
- Product Launch Date must exist for lifecycle assignment.  
- Phase classification must cover 100 % of portfolio.  
- Missing cost components default to zero (flagged 'Incomplete').  
- Referential integrity >= 99.9 % across Date/Product/Org.  
- Phase transitions validated quarterly.

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
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
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

## 13. Related Processes
Portfolio Management -> Product Development -> Category Planning -> Pricing & Promotion Strategy.

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../../04_Corporate_and_Strategy/COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "03.11.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
required_kpi_ids: []
required_kpis: {}
---

_Last updated: 03.11.2025_

