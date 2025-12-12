# COM-004 - Promotion Effectiveness  
## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-004
- **Domain:** Commercial
- **Business Owner:** CMO / Trade Marketing Lead
- **KPI Owner:** Revenue Growth Management / Commercial Controlling
- **Decision Owner:** Sales & Marketing Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Business Summary
**Purpose:** Improve promotion ROI by measuring true incremental sales and margin, controlling leakage, and optimising promo mechanics.  
**Business Value:** Fewer unprofitable promos; higher incremental GM; better channel/product targeting; reduced cannibalization.  
**Out of Scope:** Long-term pricing strategy (COM-002); assortment optimisation; omni-channel mix (COM-009).

---

## 2. Core Business Questions
- Which promotions generated true incremental sales and gross margin?
- Which channels/products deliver the highest promo ROI and uplift?
- How much did discounts erode price realization and GM?
- What promo depth/timing/mechanics should we standardize or stop?
- Where do cannibalization or leakage offset uplift?

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: sales.promo.roi.pct
    name: Promotion ROI %
    purpose: Profitability of promotions
    definition_short: Incremental GM / Promo Cost
    unit: "%"
    grain: promotion
    agg: avg
    target: >= 120%
    interpretation: Below target implies unprofitable promo
    lineage: fact_sales[Incremental GM], fact_promo[Promo Cost]
  - id: sales.promo.incremental.amount
    name: Incremental Sales Amount
    purpose: Uplift sizing
    definition_short: Sales with promo - baseline sales
    unit: "EUR"
    grain: promotion
    agg: sum
    target: Positive with ROI on/above target
    interpretation: Must offset discounts and cannibalization
    lineage: fact_sales[Net Sales Amount], baseline model
  - id: margin.promo.gm.pct
    name: Promo Gross Margin %
    purpose: Profit quality during promos
    definition_short: Gross Margin / Net Sales during promo
    unit: "%"
    grain: promotion
    agg: avg
    target: Category target (e.g., 20–25%)
    interpretation: Low indicates price/mix leakage
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], promo flag
  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    definition_short: Net Price / List Price
    unit: "%"
    grain: promotion
    agg: avg
    target: 90–95% depending on policy
    interpretation: Low shows excessive discounting
    lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount]
  - id: sales.promo.cannibalization.pct
    name: Cannibalization %
    purpose: Net effect on portfolio
    definition_short: (Sales lost in non-promoted items) / Promo uplift
    unit: "%"
    grain: promotion
    agg: avg
    target: <= 20%
    interpretation: High cannibalization reduces net benefit
    lineage: baseline vs promo comparison across related items
```

---

## 4. Business Logic & Thresholds
- Flag promotions with ROI < 120% or negative incremental GM.
- Flag excessive discounting: Price Realization % below policy and GM % below target.
- Flag high cannibalization > 20% of uplift.
- Prioritize stop/replace actions for mechanics with repeated underperformance.

```yaml
triggers:
  - kpi: sales.promo.roi.pct
    condition: below_target
    threshold: 1.2
    scope: promotion
    exclusion: strategic_brand_building
    action_code: PC2
  - kpi: sales.price.realization_pct
    condition: below_target
    threshold: 0.9
    scope: promotion
    exclusion: none
    action_code: P2
  - kpi: sales.promo.cannibalization.pct
    condition: above_target
    threshold: 0.2
    scope: promotion
    exclusion: halo/brand_build exceptions
    action_code: M3
  - kpi: margin.promo.gm.pct
    condition: below_target
    threshold: category_target
    scope: promotion
    exclusion: approved strategic promos
    action_code: D1
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| PC2 | Promo Calendar Discipline | ROI < target or repeated underperformance | Reduce low-ROI promos, re-sequence calendar | Improve ROI, protect GM | L2 | Trade Marketing |
| P2 | Margin Realisation Guardrails | Price Realization % below policy | Tighten discounting, enforce floor prices/approvals | Improve Price Realization %, GM % | L2 | Pricing / Sales Ops |
| M3 | Mix Optimisation | Cannibalization high or adverse mix | Shift to higher-margin SKUs/regions, adjust assortment | Improve Mix Effect, GM % | L2 | Category Mgmt |
| D1 | Cost Take-Out / COGS Control | Promo GM % below target due to cost | Negotiate supplier terms, optimise logistics | Improve Promo GM % | L2 | Procurement / Ops |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Promotion ROI %  
- Incremental Sales Amount  
- Promo Gross Margin %  
- Price Realization %  
- Cannibalization %  

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Promo ROI by Channel | Column | Channel | Promo ROI % | Region | Current quarter | Rank promos |
| Incremental Sales vs Baseline | Column | Promotion | Incremental Sales Amount | Category | Current period | Baseline vs actual |
| Price Realization Ladder | Waterfall | Price components | Net vs List | Channel | Current quarter | Show discount/rebate/surcharge |
| Cannibalization vs Uplift | Scatter | Cannibalization % | Incremental Sales Amount | Category/Region | Current period | Identify harmful promos |

### 6.3 Required Slicers (Mandatory)
- Date/Promo period  
- Region / Channel  
- Product Category / Subcategory  
- Promotion Type/Mechanic  

### 6.4 300-Second Layer (Diagnostics)
- Promo-level GM bridge (uplift vs cost vs leakage).
- Cannibalization root-cause table (related SKUs, categories).
- Mechanic depth/timing analysis by channel/category.

---

## 7. Data Requirements Summary
```yaml
required_facts:
  - fact_sales
  - fact_promo
required_dimensions:
  - dim_date
  - dim_org
  - dim_product
  - dim_promo
  - security_user_org
required_grain: promotion (with invoice_line base for uplift/realization)
required_time_range: 12–24 months of promo history with baseline
required_slicers: Date/Promo period, Region/Channel, Product Category/Subcategory, Mechanic
```

---

## 8. Dependencies, Assumptions & Constraints
- Baseline model for incremental sales defined and stable; uplift calculations align with COM-001/002.
- Discount components (net/list, rebates, surcharges) available to compute price realization during promos.
- Cannibalization logic depends on related items/product hierarchy.
- Conformed dims (Date, Org, Product, Promo, security_user_org) required; promo calendar/timing accurate.

---

## 9. Success Criteria
- Impact: Higher promo ROI (>=120%), higher incremental GM, reduced cannibalization.
- Adoption: Used in promo/post-event reviews; actions logged via Action Codes.
- Quality: Uplift and ROI reconcile to baseline and costs; definitions aligned with COM-001/002.
- Decision Frequency: Promo cycle (pre/post) and monthly reviews.

---

## 10. Risks & Wrong Interpretations (Short)
- Baseline mis-specified leading to overstated uplift/ROI.
- Ignoring cannibalization/halo effects distorts net benefit.
- Over-discounting to lift volume without GM guardrails.

---
