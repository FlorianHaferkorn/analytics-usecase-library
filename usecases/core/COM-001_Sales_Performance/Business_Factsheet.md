# COM-001 — Sales Performance vs Plan & LY  
## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-001
- **Domain:** Commercial
- **Business Owner:** CCO / Head of Sales
- **KPI Owner:** Commercial Controlling Lead
- **Decision Owner:** Sales Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Descriptive / Diagnostic
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Business Summary
**Purpose:** Explain Net Sales performance vs Plan and vs Last Year by price, volume, mix, and channel/region to protect revenue and margin.  
**Business Value:** Faster detection of revenue gaps; targeted pricing and mix actions to stabilise gross margin; focus resources on the most material regions/channels.  
**Out of Scope:** Promotion ROI deep dives (COM-004); detailed margin leakage diagnostics (COM-002); pipeline/win-loss (COM-010).

---

## 2. Core Business Questions
- Where do Net Sales deviate most vs Plan and vs LY by region, channel, and product hierarchy?
- What is the contribution of price, volume, and mix to the Net Sales gap?
- Which customer or product segments drive negative gross margin %?
- Which actions (pricing, mix, volume activation) close the largest gaps fastest?
- How persistent are the gaps over the last 3 months and current quarter?

**Example Query Patterns (optional):**
- “How did Net Sales vs Plan develop across Region/Channel over the last 3 months?”
- “How much of the Net Sales gap is price vs volume vs mix by region?”

---

## 3. Required KPIs (Mandatory)
All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: sales.net_sales.amount
    name: Net Sales Amount
    purpose: Core revenue control
    definition_short: Sum of net sales after discounts
    unit: €
    grain: month
    agg: sum
    target: Meet/beat Plan and LY
    interpretation: Negative gap signals revenue risk
    lineage: fact_sales[Net Sales Amount] x dim_date, dim_org, dim_product
  - id: sales.net_sales.delta_pct.plan
    name: Net Sales Δ% vs Plan
    purpose: Execution vs Plan
    definition_short: (Net Sales - Plan) / Plan
    unit: %
    grain: month
    agg: avg
    target: ≥ -2%
    interpretation: Below guardrail shows miss vs Plan
    lineage: fact_sales[Net Sales Amount], fact_sales[Plan Sales Amount]
  - id: sales.net_sales.delta_pct.ly
    name: Net Sales Δ% vs LY
    purpose: Growth vs LY
    definition_short: (Net Sales - LY) / LY
    unit: %
    grain: month
    agg: avg
    target: ≥ +3–5%
    interpretation: Negative YoY signals deterioration
    lineage: fact_sales[Net Sales Amount], fact_sales[Last Year Sales Amount]
  - id: margin.gm.pct
    name: Gross Margin %
    purpose: Profitability quality
    definition_short: Gross Margin / Net Sales
    unit: %
    grain: month
    agg: avg
    target: ≥ 25%
    interpretation: Compression shows price/mix pressure
    lineage: fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount]
  - id: sales.pvm.price_effect.amount
    name: Price Effect
    purpose: Driver analysis
    definition_short: Net Sales impact from price change
    unit: €
    grain: month
    agg: sum
    target: 0 unless price change
    interpretation: Negative implies price dilution
    lineage: fact_sales[Net Price Amount], fact_sales[Plan Sales Amount], fact_sales[Quantity]
  - id: sales.pvm.volume_effect.amount
    name: Volume Effect
    purpose: Driver analysis
    definition_short: Net Sales impact from volume change
    unit: €
    grain: month
    agg: sum
    target: 0 unless volume change
    interpretation: Negative implies demand/availability issue
    lineage: fact_sales[Quantity], fact_sales[Plan Sales Amount]
  - id: sales.pvm.mix_effect.amount
    name: Mix Effect
    purpose: Driver analysis
    definition_short: Net Sales impact from mix change
    unit: €
    grain: month
    agg: sum
    target: ≥ 0
    interpretation: Negative implies adverse mix
    lineage: fact_sales[Net Sales Amount], PVM decomposition residual
```

---

## 4. Business Logic & Thresholds
Formal rules that define performance and action triggers.

### 4.1 Logic Description
- Flag if Net Sales Δ% vs Plan < -2% for 2 consecutive months.
- Escalate if Net Sales Δ% vs LY < 0 for current quarter in top 5 regions.
- Flag GM % < 25% combined with negative Price Effect.
- Prioritise mix remediation when Mix Effect < 0 for top 5 regions/channels.

### 4.2 Formal Trigger Rules (Machine-Readable)
```yaml
triggers:
  - kpi: sales.net_sales.delta_pct.plan
    condition: <
    threshold: -0.02
    scope: last_2_months
    exclusion: none
    action_code: P2
  - kpi: sales.net_sales.delta_pct.plan
    condition: <
    threshold: -0.02
    scope: top5_regions
    exclusion: none
    action_code: V1
  - kpi: sales.pvm.price_effect.amount
    condition: <
    threshold: 0
    scope: current_quarter
    exclusion: none
    action_code: P2
  - kpi: sales.pvm.mix_effect.amount
    condition: <
    threshold: 0
    scope: top5_regions_channels
    exclusion: none
    action_code: M3
```

---

## 5. Action Codes (Mandatory)
Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|-----------------|-------------|---------------------|------------------|-------|
| P2 | Price Realisation Guardrails | sales.pvm.price_effect.amount < 0 AND margin.gm.pct < 0.25 | Tighten discounting, enforce floors and approvals | Improve Price Effect, stabilise GM % | L2 | Sales Ops / Pricing |
| V1 | Volume Activation | sales.pvm.volume_effect.amount < 0 AND sales.net_sales.delta_pct.plan < -0.02 | Targeted campaigns, fix stock availability | Increase Volume Effect, close Net Sales gap | L2 | Sales & Supply |
| M3 | Mix Optimisation | sales.pvm.mix_effect.amount < 0 | Shift to higher-margin SKUs/regions; adjust assortment | Improve Mix Effect, GM % | L2 | Category Mgmt |
| PC2 | Promo Calendar Discipline | sales.net_sales.delta_pct.plan < 0 AND promo ROI low | Reduce low-ROI promos; re-sequence calendar | Stabilise GM %, protect Net Sales | L2 | Trade Marketing |

---

## 6. 3–30–300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)
- Net Sales Amount  
- Net Sales Δ% vs Plan  
- Net Sales Δ% vs LY  
- Gross Margin %  
- Price/Volume/Mix Effects (delta summary)

### 6.2 30-Second Layer (Main Visuals)
| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Net Sales vs Plan/LY Trend | Line | dim_date[Month] | [Net Sales Amount], [Plan], [LY] | Region/Channel | Last 12–24 months | Core trend |
| PVM Bridge | Waterfall | Driver (Price/Volume/Mix) | [Net Sales Impact] | Region | Current period | Drill by Region/Channel |
| GM % Ranking | Bar (horizontal) | dim_org[Channel] | [Gross Margin %] | Region | None | Top/Bottom N |
| Gap Heatmap | Matrix | dim_org[Region] | [Net Sales Δ% Plan], [GM %] | Channel | Current quarter | Focus by geography |

### 6.3 Required Slicers (Mandatory)
- Date (Month/Quarter)  
- Region / Country / Channel  
- Product Category / Subcategory  

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
required_grain: invoice_line
required_time_range: 24 months history + Plan/LY snapshots
required_slicers: Date, Region/Country/Channel, Product Category/Subcategory
```

---

## 8. Dependencies, Assumptions & Constraints
- Plan and LY snapshots frozen at month-end; consistent currency.
- PVM decomposition requires stable product hierarchy and price logic.
- Channel/Region definitions aligned to dim_org; promotions aligned to COM-004.
- Data latency ≤24h; alignment with OneLake canonical dims (dim_date, dim_org, dim_product, security_user_org).

---

## 9. Success Criteria
- Impact: Reduce negative Net Sales vs Plan gaps by >50% within 2 quarters in top regions; improve GM % by ≥1.5 pp where price effect was negative.
- Adoption: Used in monthly commercial reviews in all regions (>80% attendance); Action Codes triggered with <5% false positives.
- Quality: No KPI-definition conflicts; refreshed monthly with <24h latency.
- Decision Frequency: Monthly and quarterly business reviews.

---

## 10. Risks & Wrong Interpretations (Short)
- Misreading price effect when promotions are not properly flagged (see COM-004).
- Attribution errors if Plan/LY versions are not frozen consistently.
- Overreacting to short-term mix swings; apply rolling view and materiality thresholds.
