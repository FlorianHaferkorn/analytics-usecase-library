# COM-002 – Margin & Price Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** COM-002
- **Domain:** Commercial
- **Owner (Business):** CCO / Pricing Lead
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** semantic_models/core_action_ready/commercial_sales/model_definition.yaml

---

## 1. Summary
**Purpose:** Protect and improve gross margin by explaining leakage across price, mix, and cost.  
**Business Value:** +0.5–1.5 pp GM%, better discount discipline, clearer mix and cost levers.  
**Out of Scope:** Long-term list price strategy; promo ROI (covered in COM-004).

---

## 2. Core Questions
- Where is gross margin eroding vs Plan and vs LY?
- Which products/channels/regions drive negative price/mix?
- How do discounts, rebates, and surcharges affect realized price?
- Which cost components or suppliers dilute margin?
- Which actions move GM fastest?

**Example Queries:**  
- “Which top-10 SKUs by channel drive the biggest GM vs Plan gap?”  
- “Where is price realization <95 % with stable volume?”  

---

## 3. KPI Set (Business View)

| KPI Name              | KPI ID (mandatory)           | Purpose                      | Definition (short)                      | Unit / Format | Target / Threshold      | Interpretation                  |
|-----------------------|------------------------------|------------------------------|-----------------------------------------|---------------|-------------------------|---------------------------------|
| Gross Margin %        | margin.gm.pct                | Profitability quality        | (Net Sales – COGS) / Net Sales         | %             | ≥ plan; no negative trend | Margin health                   |
| Gross Margin Amount   | margin.gm.amount             | GM value                     | Net Sales – COGS                       | €             | ≥ plan                   | Value impact                    |
| Price Realization %   | sales.price.realization_pct  | Discount discipline          | Net Price / List Price                 | %             | ≥95 % priority segments  | Discount leakage indicator      |
| Mix Effect Amount     | sales.mix_effect.amount      | Portfolio quality            | Impact of mix shifts on GM             | €             | ≥0 or improving         | High/low margin mix             |
| COGS per Unit         | cost.cogs_per_unit.amount    | Cost efficiency              | COGS / Units sold                      | €/unit        | ≤ plan                  | Procurement/production pressure |
| GM vs Plan %          | margin.gm.vs_plan.pct        | Target attainment            | (GM – GM Plan) / GM Plan               | %             | ± band; >0 preferred    | Gap to plan                     |

> Do: keep KPI IDs aligned to catalog; set explicit targets/bands.  
> Don’t: use raw technical fields as KPIs.

---

## 4. Business Logic & Thresholds
- GM % drop >1 pp for 2 periods → investigate price & mix.
- Price Realization % <95 % with stable volume → discount leakage alert.
- Mix Effect negative while volume grows → wrong assortment focus.
- COGS per Unit +5 % vs Plan → procurement escalation.

**Trigger (formal):**
```
WHEN margin.gm.vs_plan.pct < -1 pp
OR   sales.price.realization_pct < 95 %
OR   cost.cogs_per_unit.amount > plan + 5 %
THEN propose P2/M3/PC2/D1 as applicable
```

---

## 5. Action Codes

| Code | Name                    | Trigger (formal, KPIs)                  | Description (business action)                 | Expected KPI Impact      |
|------|-------------------------|-----------------------------------------|-----------------------------------------------|--------------------------|
| P2   | Price Adjustment        | price.realization_pct < 95 %            | Reduce leakage; align net price to value      | +0.3–0.7 pp GM %         |
| M3   | Mix Shift               | mix_effect.amount < 0                   | Push higher-margin products/segments          | +0.2–0.5 pp GM %         |
| PC2  | Cost Out / Re-Negotiate | cogs_per_unit.amount > plan +5 %        | Revisit supplier terms/BOM/logistics          | -2–4 % unit cost         |
| D1   | Demand Stimulation      | volume flat, mix improving              | Target demand in high-margin areas            | Stabilize NS + GM %      |

> Do: reference ActionCodes_Portfolio; keep triggers KPI-based.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards – mandatory)
- GM %, GM vs Plan %, Price Realization %, Mix Effect, COGS/Unit.

### 6.2 30-Second Layer (Main Visuals – mandatory)
| Visual Name        | Type      | X-Axis / Category      | Y-Axis / Value                                  | Segment / Legend | Filters          |
|--------------------|-----------|------------------------|-------------------------------------------------|------------------|------------------|
| GM Trend vs Plan   | Line      | dim_date[Month]        | [Gross Margin %], [GM vs Plan %], Plan          | Region/Channel   | Last 12–24M      |
| GM by Product/Ch   | Bar       | dim_product[Category] / dim_org[Channel] | [Gross Margin %], [Price Realization %]        | Region           | Top/Bottom N     |
| GM Variance Bridge | Waterfall | Drivers (Price, Volume, Mix, Cost)       | Δ GM vs Plan/LY                                 | n/a              | Period selector  |
| Detail Matrix      | Matrix    | Region → Channel → Product | GM %, Price Realization %, COGS/Unit, Mix Effect | Region/Channel   | Export enabled   |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill paths: Region → Channel → Product; Brand/Category as needed.
- Exports: variance table with drivers; action list per owner.

---

## 7. Dependencies, Assumptions & Constraints
- Data: list/net price, discount/surcharge, COGS, plan GM% and plan GM amount; stable product and org hierarchies.
- Assumptions: Plan values frozen post-close; consistent BOM/COGS granularity.
- Constraints: Missing plan/target fields reduce insight quality; ensure PVM template alignment.

---

## 8. Success Criteria
- Leading: >80 % usage in monthly commercial/finance reviews; action list maintained.
- Lagging: GM % improves vs Plan/LY; Price Realization % ≥95 % in priority segments; unit cost reduced where targeted.
- Cadence/Quality: Monthly review; no KPI definition conflicts.
