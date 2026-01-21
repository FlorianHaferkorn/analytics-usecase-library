---
id: COM-004
factsheet_type: business
---

# COM-004 - Promotion Effectiveness  

## Business Factsheet

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
    target: Category target (e.g., 20-25%)
    interpretation: Low indicates price/mix leakage
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount], promo flag

  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    definition_short: Net Price / List Price
    unit: "%"
    grain: promotion
    agg: avg
    target: 90-95% depending on policy
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

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: C-M2.1
    name: Price Realization Guardrails
    purpose: Stop Discount Leakage
    status: active
    owner: Pricing Lead
    trigger_kpis: [sales.price.realization_pct]
    guardrail_kpis: [margin.gm.pct]
    outcome_kpis: [sales.price.realization_pct, margin.gm.pct]
    impact_range: sales.price.realization_pct: 1.0-3.0 pp
    levels: L1-L3
    definition: framework\action_codes\Commercial\C-M2.1.yaml

  - id: C-S1.1
    name: Price Discipline Enforcement
    purpose: Protect Gross Margin
    status: active
    owner: Pricing Manager
    trigger_kpis: [margin.gm.pct, sales.pvm.price_effect.amount]
    guardrail_kpis: [sales.net_sales.delta_pct.plan]
    outcome_kpis: [margin.gm.pct]
    impact_range: margin.gm.pct: 0.5-1.5 pp
    levels: L1-L3
    definition: framework\action_codes\Commercial\C-S1.1.yaml

  - id: C-M2.2
    name: Mix Optimization (Margin-Driven)
    purpose: Improve Margin via Sales Mix Quality
    status: active
    owner: Category Manager
    trigger_kpis: [sales.pvm.mix_effect.amount]
    guardrail_kpis: [margin.gm.pct]
    outcome_kpis: [margin.gm.pct, sales.pvm.mix_effect.amount]
    impact_range: margin.gm.pct: 0.3-1.2 pp
    levels: L1-L3
    definition: framework\action_codes\Commercial\C-M2.2.yaml

  - id: C-P4.1
    name: Promo Calendar Discipline
    purpose: Eliminate Structurally Unprofitable Promotions
    status: active
    owner: Trade Marketing Lead
    trigger_kpis: [sales.promo.roi.pct]
    guardrail_kpis: [margin.promo.gm.pct]
    outcome_kpis: [sales.promo.roi.pct, margin.promo.gm.pct]
    impact_range: sales.promo.roi.pct: 5.0-20.0 pp
    levels: L1-L3
    definition: framework\action_codes\Commercial\C-P4.1.yaml

  - id: C-S1.2
    name: Sales Gap Recovery via Price & Pack Adjustment
    purpose: Close Plan Gaps Without Margin Erosion
    status: active
    owner: Sales Director
    trigger_kpis: [sales.net_sales.delta_pct.plan]
    guardrail_kpis: [margin.gm.pct]
    outcome_kpis: [sales.net_sales.amount]
    impact_range: sales.net_sales.amount: 1.0-3.0 %
    levels: L1-L3
    definition: framework\action_codes\Commercial\C-S1.2.yaml
```

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

## 6. Data Requirements Summary

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
required_time_range: 12-24 months of promo history with baseline
required_slicers: Date/Promo period, Region/Channel, Product Category/Subcategory, Mechanic
```

---

## 7. Dependencies, Assumptions & Constraints

- Baseline model for incremental sales defined and stable; uplift calculations align with COM-001/002.
- Discount components (net/list, rebates, surcharges) available to compute price realization during promos.
- Cannibalization logic depends on related items/product hierarchy.
- Conformed dims (Date, Org, Product, Promo, security_user_org) required; promo calendar/timing accurate.

---

## 8. Success Criteria

- Impact: Higher promo ROI (>=120%), higher incremental GM, reduced cannibalization.
- Adoption: Used in promo/post-event reviews; actions logged via Action Codes.
- Quality: Uplift and ROI reconcile to baseline and costs; definitions aligned with COM-001/002.
- Decision Frequency: Promo cycle (pre/post) and monthly reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Baseline mis-specified leading to overstated uplift/ROI.
- Ignoring cannibalization/halo effects distorts net benefit.
- Over-discounting to lift volume without GM guardrails.

---


