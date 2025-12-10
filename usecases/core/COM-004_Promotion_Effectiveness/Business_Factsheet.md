# COM-004 — Promotion Effectiveness  
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
**Out of Scope:** Long-term pricing strategy (COM-002); assortment optimisation (separate UC); omni-channel mix (COM-009).

---

## 2. Core Business Questions
- Which promotions generated true incremental sales and gross margin?
- Which channels/products deliver the highest promo ROI and uplift?
- How much did discounts erode price realization and GM?
- What promo depth/timing/mechanics should we standardize or stop?
- Where do cannibalization or leakage offset uplift?

**Example Query Patterns (optional):**
- “Which top 10 promos by channel delivered ROI >120% and uplift >5%?”  
- “Which mechanics drive lowest leakage and best ROI for category X?”

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: sales.promo.roi.pct
    name: Promotion ROI %
    purpose: Profitability of promotions
    definition_short: Incremental GM / Promo Cost
    unit: %
    grain: promotion
    agg: avg
    target: ≥ 120%
    interpretation: <target implies unprofitable promo
    lineage: fact_sales[Incremental GM], fact_promo[Promo Cost]
  - id: sales.promo.incremental.amount
    name: Incremental Sales Amount
    purpose: Uplift sizing
    definition_short: Sales with promo – baseline sales
    unit: €
    grain: promotion
    agg: sum
    target: Positive with ROI ≥ target
    interpretation: Must offset discounts and cannibalization
    lineage: fact_sales[Net Sales Amount], baseline model
  - id: margin.promo.gm.pct
    name: Promo Gross Margin %
    purpose: Profit quality during promos
    definition_short: Gross Margin / Net Sales during promo
    unit: %
    grain: promotion
    agg: avg
    target: ≥ 20–25% depending on category
    interpretation: Low indicates price/mix leakage
    lineage: fact_sales[Net Sales Amount], fact_sales[COGS], promo flag
  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    definition_short: Net Price / List Price
    unit: %
    grain: promotion
    agg: avg
    target: ≥ 90–95% depending on policy
    interpretation: Low shows excessive discounting
    lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount]
  - id: sales.promo.cannibalization.pct
    name: Cannibalization %
    purpose: Net effect on portfolio
    definition_short: (Sales lost in non-promoted items) / Promo uplift
    unit: %
    grain: promotion
    agg: avg
    target: ≤ 20%
    interpretation: High cannibalization reduces net benefit
    lineage: baseline vs promo comparison across related items
```

---

## 4. Business Logic & Thresholds
Formal rules that define performance and action triggers.

### 4.1 Logic Description
- Flag promotions with ROI < 120% or negative incremental GM.
- Flag excessive discounting: Price Realization % < policy threshold and GM % < target.
- Flag high cannibalization > 20% of uplift.
- Prioritize stop/replace actions for mechanics with repeated underperformance.

### 4.2 Formal Trigger Rules (Machine-Readable)
```yaml
triggers:
  - kpi: sales.promo.roi.pct
    condition: <
    threshold: 1.2
    scope: promotion
    exclusion: strategic_brand_building
    action_code: PC2
  - kpi: sales.price.realization_pct
    condition: <
    threshold: 0.9
    scope: promotion
    exclusion: none
    action_code: P2
  - kpi: sales.promo.cannibalization.pct
    condition: >
    threshold: 0.2
    scope: related_items
    exclusion: none
    action_code: M3
  - kpi: margin.promo.gm.pct
    condition: <
    threshold: category_target
    scope: promotion
    exclusion: launch_promos
    action_code: PC2
```

---

## 5. Action Codes (Mandatory)
Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| PC2 | Promo Calendar Discipline | sales.promo.roi.pct < 1.2 OR margin.promo.gm.pct below target | Stop/replace low-ROI promos; re-sequence calendar | Improve ROI %, GM % | L2 | Trade Marketing |
| P2 | Price Realisation Guardrails | sales.price.realization_pct < threshold | Tighten discount depth, approvals, floors | Improve price realization, GM % | L2 | Pricing / Sales Ops |
| M3 | Mix Optimisation | sales.promo.cannibalization.pct > 0.2 | Shift assortment to reduce cannibalization, favor accretive SKUs | Reduce cannibalization, raise GM % | L2 | Category Mgmt |
| D1 | Cost Take-Out / COGS Control | Promo GM loss driven by cost | Reduce promo funding costs, negotiate vendor funding | Lower cost, improve GM % | L2 | Procurement |

---

## 6. 3–30–300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Promotion ROI %  
- Incremental Sales Amount  
- Promo Gross Margin %  
- Price Realization %  
- Cannibalization %  

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Promo ROI vs Target | Column | dim_promo[Promotion] | [Promo ROI %], [Target] | Channel/Category | Current quarter | Highlight underperformers |
| Incremental Sales & GM Bridge | Waterfall | Driver (List/Discount/Volume/Mix) | [Incremental Sales/GM] | Channel | Current period | Decompose uplift |
| Price Realization During Promo | Column | dim_promo[Promotion] | [Price Realization %] | Channel | Current quarter | Guardrails |
| Cannibalization vs Uplift | Scatter | [Cannibalization %] | [Incremental Sales Amount] | Category | Current quarter | Identify harmful promos |

### 6.3 Required Slicers (Mandatory)
- Date/Promo Period  
- Region / Channel  
- Category / Product  
- Promotion Type/Mechanic  

---

## 7. Data Requirements Summary
```yaml
required_facts:
  - fact_sales (with promo flags)
  - fact_promo (calendar/costs)
required_dimensions:
  - dim_date
  - dim_org
  - dim_product
  - dim_promo
  - security_user_org
required_grain: invoice_line for sales; promotion for ROI
required_time_range: Last 12–24 months of promos
required_slicers: Date/Promo period, Region/Channel, Category/Product, Promo Type
```

---

## 8. Dependencies, Assumptions & Constraints
- Baseline/uplift methodology agreed and consistent; cannibalization measured on related items.
- Promo costs captured (trade spend/funding); price realization available.
- Alignment with COM-002 on price realization and GM definitions.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 9. Success Criteria
- Impact: Increase share of promos with ROI ≥ 120%; reduce low-ROI promos by >30%; lift promo GM % to target bands.  
- Adoption: Used in quarterly promo planning and post-event reviews; action codes triggered with <5% false positives.  
- Quality: Uplift/cannibalization reconciles to sales totals; consistent KPI definitions across COM-001/002/004.  
- Decision Frequency: Quarterly planning; monthly post-event review.

---

## 10. Risks & Wrong Interpretations (Short)
- Misattributing uplift without proper baseline control groups.  
- Understating cannibalization across related categories.  
- Ignoring vendor funding/COGS timing leading to wrong ROI.  
