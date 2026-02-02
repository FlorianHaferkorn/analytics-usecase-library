---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

# COM-004 - Promotion Effectiveness  

## Business Factsheet

---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

## 1. Business Summary

**Purpose:** Improve promotion ROI by measuring true incremental sales and margin, controlling leakage, and optimising promo mechanics.  
**Business Value:** Fewer unprofitable promos; higher incremental GM; better channel/product targeting; reduced cannibalization.  
**Out of Scope:** Long-term pricing strategy (COM-002); assortment optimisation; omni-channel mix (COM-009).

---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: sales.promo.roi.pct
    kpi_catalog_id: Profitability
    name: Promotion ROI %
    purpose: Profitability of promotions
    agg: avg

  - id: sales.promo.incremental.amount
    name: Incremental Sales Amount
    purpose: Uplift sizing
    agg: sum

  - id: margin.promo.gm.pct
    name: Promo Gross Margin %
    purpose: Profit quality during promos
    agg: avg

  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    agg: avg

  - id: sales.promo.cannibalization.pct
    name: Cannibalization %
    purpose: Net effect on portfolio
    agg: avg
```

---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Promotion ROI %  
- Incremental Sales Amount  
- Promo Gross Margin %  
- Price Realization %  
- Cannibalization %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Promo ROI by Channel | Column | Channel | Promo ROI % | Region | Current quarter | Rank promos |
| Incremental Sales vs Baseline | Column | Promotion | Incremental Sales Amount | Category | Current period | Baseline vs actual |
| Price Realization Ladder | Waterfall | Price components | Net vs List | Channel | Current quarter | Show discount/rebate/surcharge |
| Cannibalization vs Uplift | Scatter | Cannibalization % | Incremental Sales Amount | Category/Region | Current period | Identify harmful promos |

### 5.3 Required Slicers (Mandatory)

- Date/Promo period  
- Region / Channel  
- Product Category / Subcategory  
- Promotion Type/Mechanic  

### 5.4 300-Second Layer (Diagnostics)

- Promo-level GM bridge (uplift vs cost vs leakage).
- Cannibalization root-cause table (related SKUs, categories).
- Mechanic depth/timing analysis by channel/category.

---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

## 7. Dependencies, Assumptions & Constraints

- Baseline model for incremental sales defined and stable; uplift calculations align with COM-001/002.
- Discount components (net/list, rebates, surcharges) available to compute price realization during promos.
- Cannibalization logic depends on related items/product hierarchy.
- Conformed dims (Date, Org, Product, Promo, security_user_org) required; promo calendar/timing accurate.

---
id: COM-004
factsheet_type: business
required_kpi_ids:
  - sales.promo.roi.pct
  - sales.promo.incremental.amount
  - margin.promo.gm.pct
  - sales.price.realization_pct
  - sales.promo.cannibalization.pct
---

## 9. Risks & Wrong Interpretations (Short)

- Baseline mis-specified leading to overstated uplift/ROI.
- Ignoring cannibalization/halo effects distorts net benefit.
- Over-discounting to lift volume without GM guardrails.

---




