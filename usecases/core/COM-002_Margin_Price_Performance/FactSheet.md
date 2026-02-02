---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

# COM-002 - Margin & Price Performance  

## Business Factsheet

---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

## 1. Business Summary

**Purpose:** Protect and improve gross margin by explaining leakage across price realization, mix, and unit cost.  
**Business Value:** +0.5-1.5 pp GM%, tighter discount discipline, clearer mix levers, faster correction of cost leakage.  
**Out of Scope:** Long-term list price strategy; promo ROI (COM-004); channel mix strategy (COM-009).

---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: margin.gm.pct
    kpi_catalog_id: Profitability
    name: Gross Margin %
    purpose: Profitability quality
    agg: avg

  - id: profit.gross_margin
    name: Gross Margin % (Strategic)
    purpose: Strategic profitability benchmark
    agg: avg

  - id: margin.gm.amount
    name: Gross Margin Amount
    purpose: Profit pool sizing
    agg: sum

  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    agg: avg

  - id: sales.pvm.mix_effect.amount
    name: Mix Effect Amount
    purpose: Mix quality
    agg: sum

  - id: cost.cogs_per_unit.amount
    name: COGS per Unit
    purpose: Unit cost control
    agg: avg

  - id: margin.gm.vs_plan.pct
    name: Gross Margin % vs Plan
    purpose: Performance vs Plan
    agg: avg
```

---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Gross Margin %  
- Gross Margin Amount  
- Price Realization %  
- Mix Effect Amount  
- COGS per Unit  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| GM % vs Plan Trend | Line | dim_date[Month] | GM %, Plan GM % | Region/Channel | L12-24M | Core trend |
| Price Realization by Channel | Column | dim_org[Channel] | Price Realization % | Region | Current quarter | Highlight low channels |
| Mix Effect Bridge | Waterfall | Driver (Mix) | Mix Effect Amount | Region/Channel | Current period | PVM mix focus |
| COGS per Unit vs Plan | Column | dim_product[Category] | COGS per Unit, Plan COGS per Unit | Region | Current quarter | Watch unit cost drift |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Country / Channel  
- Product Category / Subcategory  
- Customer (optional)

### 5.4 300-Second Layer (Diagnostics)

- Price realization ladder (List -> Net) with discount/rebate/surcharge.
- Mix decomposition by Region/Channel/Product.
- Unit cost variance by supplier/plant/SKU.

---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

## 7. Dependencies, Assumptions & Constraints

- Plan and LY snapshots frozen monthly; currency aligned.
- Pricing elements (list price, discounts, rebates, surcharges) must be complete for realization.
- PVM logic aligned with COM-001/004; cost attribution stable.
- Conformed dims (Date, Org, Product, security_user_org) required.

---
id: COM-002
factsheet_type: business
required_kpi_ids:
  - margin.gm.pct
  - profit.gross_margin
  - margin.gm.amount
  - sales.price.realization_pct
  - sales.pvm.mix_effect.amount
  - cost.cogs_per_unit.amount
  - margin.gm.vs_plan.pct
---

## 9. Risks & Wrong Interpretations (Short)

- Misstating realization if promo flags are missing (see COM-004).  
- Misattributing mix when hierarchy changes mid-period.  
- Ignoring cost timing effects (e.g., accruals) when reading COGS/unit trends.

---




