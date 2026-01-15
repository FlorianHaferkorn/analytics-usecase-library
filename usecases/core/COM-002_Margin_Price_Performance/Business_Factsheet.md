---
id: COM-002
factsheet_type: business
---

# COM-002 - Margin & Price Performance  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** COM-002
- **Domain:** Commercial
- **Business Owner:** CCO / Head of Pricing
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales & Pricing Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

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
    name: Gross Margin %
    purpose: Profitability quality
    definition_short: Gross Margin / Net Sales
    unit: "%"
    grain: month
    agg: avg
    target: >= 25%
    interpretation: Compression signals price/mix/cost pressure
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount]

  - id: profit.gross_margin
    name: Gross Margin % (Strategic)
    purpose: Strategic profitability benchmark
    definition_short: (Net Sales Amount - COGS Amount) / Net Sales Amount
    unit: "%"
    grain: month
    agg: avg
    target: >= 25%
    interpretation: Strategic view of gross margin health
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount]

  - id: margin.gm.amount
    name: Gross Margin Amount
    purpose: Profit pool sizing
    definition_short: Net Sales Amount - COGS Amount
    unit: "EUR"
    grain: month
    agg: sum
    target: Improve vs Plan and LY
    interpretation: Negative gap erodes profitability
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount]

  - id: sales.price.realization_pct
    name: Price Realization %
    purpose: Discount discipline
    definition_short: Net Price / List Price
    unit: "%"
    grain: month
    agg: avg
    target: >= 95%
    interpretation: Low values imply discount leakage
    lineage: fact_sales[Net Price Amount], fact_sales[List Price Amount]

  - id: sales.pvm.mix_effect.amount
    name: Mix Effect Amount
    purpose: Mix quality
    definition_short: Net Sales impact from mix change
    unit: "EUR"
    grain: month
    agg: sum
    target: >= 0
    interpretation: Negative implies adverse mix
    lineage: fact_sales[Net Sales Amount], PVM decomposition residual

  - id: cost.cogs_per_unit.amount
    name: COGS per Unit
    purpose: Unit cost control
    definition_short: COGS Amount / Quantity
    unit: "EUR"
    grain: month
    agg: avg
    target: Stable or improving vs Plan/LY
    interpretation: Increases signal cost leakage
    lineage: fact_sales[Cost of Goods Sold Amount], fact_sales[Quantity]

  - id: margin.gm.vs_plan.pct
    name: Gross Margin % vs Plan
    purpose: Performance vs Plan
    definition_short: (GM % - Plan GM %) / Plan GM %
    unit: "pp"
    grain: month
    agg: avg
    target: >= 0 pp
    interpretation: Negative variance shows miss vs Plan
    lineage: GM %, Plan GM %
```

---

## 4. Business Logic & Thresholds

### 4.1 Logic Description

### 4.2 Formal Action Code Rules (Machine-Readable)

- Flag if Price Realization % < 95% with GM % < 25%.
- Flag if Mix Effect Amount < 0 in top 5 regions/channels.
- Escalate if GM % vs Plan < 0 for 2 consecutive months.
- Highlight if COGS per Unit rising >2% vs Plan for top SKUs.

```yaml
action_codes:

  - kpi: sales.price.realization_pct
    condition: below_target
    threshold: 0.95
    scope: region_channel
    exclusion: low-volume SKUs
    action_code: C-M2.1

  - kpi: sales.pvm.mix_effect.amount
    condition: negative
    threshold: 0
    scope: top5_regions_channels
    exclusion: none
    action_code: C-M2.2

  - kpi: margin.gm.vs_plan.pct
    condition: below_target
    threshold: 0
    scope: last_2_months
    exclusion: none
    action_code: C-M2.4

  - kpi: cost.cogs_per_unit.amount
    condition: above_threshold
    threshold: 0.02   # +2% vs plan/LY
    scope: top_skus
    exclusion: new launches
    action_code: C-M2.3
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| C-M2.1 | Price Realization Guardrails | sales.price.realization_pct below_target 0.95 | Enforce discount floors; Require approvals for price exceptions | sales.price.realization_pct +1.0-3.0 pp (1-2 periods) | L1 | Commercial |
| C-M2.2 | Mix Optimization (Margin-Driven) | sales.pvm.mix_effect.amount negative 0 | Shift sales focus toward higher-margin SKUs and regions; Deprioritize structurally margin-dilutive mix components | margin.gm.pct +0.3-1.2 pp (1-3 periods) | L2 | Commercial |
| C-M2.3 | Unit Cost Leakage Correction | cost.cogs_per_unit.amount above_threshold | Initiate supplier renegotiation or sourcing actions; Correct production or logistics cost deviations | cost.cogs_per_unit.amount +1.0-4.0 % (2-6 periods) | L2 | Operations / Procurement |
| C-M2.4 | Promotion Margin Discipline | margin.gm.vs_plan.pct below_target 0 | De-prioritize or stop margin-dilutive promotions; Resequence or downscale promotion calendar | margin.gm.pct +0.2-0.8 pp (1-2 periods) | L1 | Commercial / Trade Marketing |

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Gross Margin %  
- Gross Margin Amount  
- Price Realization %  
- Mix Effect Amount  
- COGS per Unit  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| GM % vs Plan Trend | Line | dim_date[Month] | GM %, Plan GM % | Region/Channel | L12-24M | Core trend |
| Price Realization by Channel | Column | dim_org[Channel] | Price Realization % | Region | Current quarter | Highlight low channels |
| Mix Effect Bridge | Waterfall | Driver (Mix) | Mix Effect Amount | Region/Channel | Current period | PVM mix focus |
| COGS per Unit vs Plan | Column | dim_product[Category] | COGS per Unit, Plan COGS per Unit | Region | Current quarter | Watch unit cost drift |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Country / Channel  
- Product Category / Subcategory  
- Customer (optional)

### 6.4 300-Second Layer (Diagnostics)

- Price realization ladder (List -> Net) with discount/rebate/surcharge.
- Mix decomposition by Region/Channel/Product.
- Unit cost variance by supplier/plant/SKU.

---

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- Plan and LY snapshots frozen monthly; currency aligned.
- Pricing elements (list price, discounts, rebates, surcharges) must be complete for realization.
- PVM logic aligned with COM-001/004; cost attribution stable.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 9. Success Criteria

- Impact: +0.5-1.5 pp GM % improvement in targeted channels/SKUs; price realization uplift to =95%.  
- Adoption: Used in monthly pricing reviews; action codes triggered with <5% false positives.  
- Quality: Variance bridge reconciles to 100% of GM gap; no KPI-definition conflicts.  
- Decision Frequency: Monthly pricing and margin review.

---

## 10. Risks & Wrong Interpretations (Short)

- Misstating realization if promo flags are missing (see COM-004).  
- Misattributing mix when hierarchy changes mid-period.  
- Ignoring cost timing effects (e.g., accruals) when reading COGS/unit trends.

---

