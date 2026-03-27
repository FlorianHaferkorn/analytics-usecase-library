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
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Commercial.SemanticModel (domain model for COM-*).

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


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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




