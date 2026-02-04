---
id: COM-002
factsheet_type: business
---

# COM-002 - Margin & Price Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-002
- **Domain:** Commercial
- **Business Owner:** CCO / Head of Pricing
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales & Pricing Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** framework/framework/framework/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** framework/framework/framework/semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Protect and improve gross margin by explaining leakage across price realization, mix, and unit cost.  
**Business Value:** +0.5-1.5 pp GM%, tighter discount discipline, clearer mix levers, faster correction of cost leakage.  
**Out of Scope:** Long-term list price strategy; promo ROI (COM-004); channel mix strategy (COM-009).

---

## 2. Core Business Questions

- Where is gross margin eroding vs Plan and vs LY by region/channel/product?
- Which products/channels/regions drive negative price realization or adverse mix?
- How do discounts, rebates, and surcharges affect realized price?
- Which cost components or suppliers dilute margin?
- Which actions move gross margin fastest with lowest risk?

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

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

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
```

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

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_sales
required_dimensions:

  - dim_date

  - dim_org

  - dim_product

  - security_user_org
required_grain: invoice_line (aggregated to month for KPIs)
required_time_range: 24 months history + Plan/LY snapshots
required_slicers: Date, Region/Country/Channel, Product Category/Subcategory
```

---

## 7. Dependencies, Assumptions & Constraints

- Plan and LY snapshots frozen monthly; currency aligned.
- Pricing elements (list price, discounts, rebates, surcharges) must be complete for realization.
- PVM logic aligned with COM-001/004; cost attribution stable.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 8. Success Criteria

- Impact: +0.5-1.5 pp GM % improvement in targeted channels/SKUs; price realization uplift to =95%.  
- Adoption: Used in monthly pricing reviews; action codes triggered with <5% false positives.  
- Quality: Variance bridge reconciles to 100% of GM gap; no KPI-definition conflicts.  
- Decision Frequency: Monthly pricing and margin review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misstating realization if promo flags are missing (see COM-004).  
- Misattributing mix when hierarchy changes mid-period.  
- Ignoring cost timing effects (e.g., accruals) when reading COGS/unit trends.

---




