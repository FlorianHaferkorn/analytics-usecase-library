---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---
# COM-001 - Sales Performance vs Plan & LY  

## Business Factsheet

---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---

## 1. Business Summary

**Purpose:** Explain Net Sales performance vs Plan and vs Last Year by price,
volume, mix, and channel/region to protect revenue and margin.  
**Business Value:** Faster detection of revenue gaps; targeted pricing and mix
actions to stabilise gross margin; focus resources on the most material
regions/channels.  
**Out of Scope:** Promotion ROI deep dives (COM-004); detailed margin leakage
diagnostics (COM-002); pipeline/win-loss (COM-010).

---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: sales.net_sales.amount
    kpi_catalog_id: Growth
    name: Net Sales Amount
    purpose: Core revenue control
    agg: sum

  - id: sales.net_sales.delta_pct.plan
    name: Net Sales % vs Plan
    purpose: Execution vs Plan
    agg: avg

  - id: sales.net_sales.delta_pct.ly
    name: Net Sales % vs LY
    purpose: Growth vs LY
    agg: avg

  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Profitability quality
    agg: avg

  - id: sales.pvm.price_effect.amount
    name: Price Effect Amount
    purpose: Driver analysis
    agg: sum

  - id: sales.pvm.volume_effect.amount
    name: Volume Effect Amount
    purpose: Driver analysis
    agg: sum

  - id: sales.pvm.mix_effect.amount
    name: Mix Effect Amount
    purpose: Driver analysis
    agg: sum
```

---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Net Sales Amount  
- Net Sales % vs Plan  
- Net Sales % vs LY  
- Gross Margin %  
- Price/Volume/Mix Effects (cards or mini-tiles)  

### 5.2 30-Second Layer (Main Visuals)

- **Net Sales vs Plan/LY**
  - Visual Type: Line + area band
  - X-Axis: Date[Month]
  - Y-Axis: Net Sales, Plan, LY
  - Segment: Region/Channel
  - Default Filter: L12M
  - Notes: Show gaps

- **PVM Bridge**
  - Visual Type: Waterfall
  - X-Axis: Drivers
  - Y-Axis: P, V, M impact
  - Segment: Region/Channel
  - Default Filter: Current Q
  - Notes: Link to COM-002

- **GM % by Region/Channel**
  - Visual Type: Column
  - X-Axis: Region/Channel
  - Y-Axis: GM %
  - Segment: Product Tier
  - Default Filter: Current Q
  - Notes: Guardrails

- **Top/Bottom Segments**
  - Visual Type: Bar (rank)
  - X-Axis: Region/Channel/Segment
  - Y-Axis: Net Sales Gap
  - Segment: Product
  - Default Filter: Current Q
  - Notes: Focus list

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Channel  
- Product Category  
- Customer Segment (optional)

### 5.4 300-Second Layer (Diagnostics)

- PVM decomposition by Region/Channel/Product.
- Margin guardrail table (GM %, discount discipline).
- Top-N accounts/products with adverse price/mix effects.

---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---

## 7. Dependencies, Assumptions & Constraints

- Plan and LY fields must be populated in fact_sales (Plan Sales Amount,
  Last Year Sales Amount).
- PVM requires Net Price Amount, Plan Sales Amount, Quantity and residual logic
  alignment with COM-002.
- Gross Margin uses COGS; returns/credit notes handled upstream.
- Conformed dims (Date, Org, Product, security_user_org) required.

---
id: COM-001
factsheet_type: business
required_kpi_ids:
  - sales.net_sales.amount
  - sales.net_sales.delta_pct.plan
  - sales.net_sales.delta_pct.ly
  - margin.gm.pct
  - sales.pvm.price_effect.amount
  - sales.pvm.volume_effect.amount
  - sales.pvm.mix_effect.amount
---

## 9. Risks & Wrong Interpretations (Short)

- Misstated Plan/LY leading to false gaps.
- PVM residual too high due to inconsistent plan price or quantity.
- Over-reacting on price without GM guardrails can erode margin.

---



