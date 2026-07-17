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
- **Related Data Contract:** core/data_contracts/domains/commercial_sales.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Implementation: products/fabric/powerbi/dist/Commercial.SemanticModel (domain model for COM-*).

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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| margin.gm.pct | Strategic |
| margin.gm.amount | Influencing |
| sales.price.list.amount | Influencing |
| sales.price.net.amount | Influencing |
| sales.price.realization_pct | Influencing |
| sales.pvm.mix_effect.amount | Influencing |
| cost.cogs_per_unit.amount | Influencing |
| margin.gm.vs_plan.pct | Influencing |
| cost.cogs.amount | Supporting |
| sales.promo.baseline_sales.amount | Supporting |
| sales.promo.cost.amount | Supporting |
| sales.promo.incremental_gm.amount | Supporting |
| sales.pvm.price_effect.amount | Supporting |
| sales.pvm.volume_effect.amount | Supporting |

**Action Codes:** C-M2.2, C-P4.1, C-S1.2

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

### 3.1 Standards basis

The headline KPIs reference these external standards — *reference, don't redefine* (full alignment & drift audit under `core/kpi_catalog/standards/`):

- **Gross Margin %** (`margin.gm.pct`) → **ESMA-APM** (partial): A ratio of two IFRS figures (IFRS 15 revenue, IAS 2 cost of sales); the percentage itself is a non-GAAP APM.
- **Gross Margin % vs Plan** (`margin.gm.vs_plan.pct`) → **IFRS IAS 1** (none): Internal budget-variance metric; no external standard.
- **Price Realization %** (`sales.price.realization_pct`) → **IFRS 15** (none): Price realization (net/list) is a management pricing metric, not IFRS-defined.
- **Gross Margin Amount** (`margin.gm.amount`) → **IFRS IAS 1** (partial): Gross profit (Revenue − Cost of sales) is an illustrative IAS 1 by-function subtotal, not a mandated line item.
- **List Price Amount** (`sales.price.list.amount`) → **IFRS 15** (none): List price is a pre-discount catalogue figure — an input to discount/realization analysis, not an IFRS 15 figure (IFRS 15 measures the transaction price actually expected).
- **Net Price Amount** (`sales.price.net.amount`) → **IFRS 15** (partial): Net price is the IFRS 15 transaction price after trade discounts and variable consideration.
- **Mix Effect Amount** (`sales.pvm.mix_effect.amount`) → **Management accounting (CIMA/IMA)** (partial): Mix effect is the residual (total − price − volume) in the standard three-way variance decomposition.
- **COGS per Unit** (`cost.cogs_per_unit.amount`) → **IFRS IAS 2** (none): Internal cost-accounting metric.

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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

- Price realization ladder from list to net with discount, rebate, and surcharge components by region, channel, and SKU cluster.
- Mix decomposition by region, channel, product category, and SKU to isolate whether margin loss is commercial mix drift or a true pricing failure.
- Unit-cost variance drill tying COGS per unit, GM vs plan, and mix effect back to the invoice-line combinations that justify C-M2.2 or C-P4.1.

---

## 6. Data Requirements Summary

- Required facts: fact_sales with list price, net price, discounts, plan, LY, quantity, and COGS detail at invoice-line level.
- Required dimensions: dim_date, dim_org, dim_product, and security_user_org.
- Required grain: invoice_line retained for diagnostics, rolled up to month for KPI monitoring.
- Required time range: 24 months history plus frozen plan and LY snapshots.
- Required slicers: Date, Region/Country/Channel, Product Category/Subcategory.

---

## 7. Dependencies, Assumptions & Constraints

- Plan and LY snapshots frozen monthly; currency aligned.
- Pricing elements (list price, discounts, rebates, surcharges) must be complete for realization.
- PVM logic aligned with COM-001/004; cost attribution stable.
- Conformed dims (Date, Org, Product, security_user_org) required.

---

## 8. Success Criteria

- **Benchmark Targets (world-class reference):** Gross Margin 25–45% for B2B manufacturing with a +0.5–1.5 pp annual improvement goal (APQC; Deloitte); Price Realization Rate ≥ 90% (Simon-Kucher Global Pricing Study 2023).  
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

## 10. Typical Decision Scenarios

### Scenario A: Price Realization Below Guardrail

**Situation:** Price realization has dropped to 92% (vs 95% guardrail) in the Southern Europe region. Discount approval logs show 15% of invoices were granted exceptions above the standard discount floor, concentrated in 3 large customers.

**Decision question:** Are the exceptions above approval authority? Is this isolated to Southern Europe or a broader pattern?

**Who decides:** Commercial Controlling Lead + Pricing Manager + Regional Sales Director.

**Consequence of inaction:** At 3pp realization shortfall on €80M regional revenue = €2.4M annual margin leakage. If normalized to full-company revenue, the impact becomes a material earnings miss.

**Action Code triggered:** C-P4.1 (Price Realization Recovery) — activates exception audit and pricing discipline review.

### Scenario B: Gross Margin Collapse in a Key Category

**Situation:** GM % in the Premium tier has dropped 4pp vs plan in the last 2 months. The margin bridge shows: price effect −1pp, mix effect −2pp (shift to lower-margin SKUs within the tier), COGS/unit effect −1pp.

**Decision question:** Which of the three effects is controllable in the near term? The COGS/unit change is expected (input cost inflation); the mix and price effects are operational decisions.

**Who decides:** CCO + Category Manager.

**Consequence of inaction:** A 4pp GM drop on €50M category revenue = €2M annualized. If COGS is structural, the mix and price response must offset it within 2 quarters.

**Action Code triggered:** C-M2.2 (Mix Recovery) and C-P4.1 (Price Recovery) — sequential activation based on root cause.

### Scenario C: Unit Cost Spike Not Explained by Volume

**Situation:** COGS/unit has risen 8% vs plan without a change in production volume. The cost bridge shows raw material cost as the driver (+6%) with overhead per unit flat.

**Decision question:** Is this a one-time procurement event or a structural input cost increase? Does the list price need to be revised to recover margin?

**Who decides:** Finance Controlling + Procurement + Pricing.

**Consequence of inaction:** Margin erodes even as revenue meets plan. The Margin-First strategy pattern requires a pricing or cost response within 2 S&OP cycles.

**Action Code triggered:** F-C1.2 (Cost Reduction) for procurement response; C-P4.1 for pricing pass-through assessment.

---




