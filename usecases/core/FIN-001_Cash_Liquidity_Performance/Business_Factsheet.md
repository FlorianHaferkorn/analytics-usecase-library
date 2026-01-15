---
id: FIN-001
factsheet_type: business
---

# FIN-001 - Cash & Liquidity Performance  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** FIN-001
- **Domain:** Finance
- **Business Owner:** CFO / Treasury Lead
- **KPI Owner:** Treasury / Finance Controlling
- **Decision Owner:** Finance Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** data_contracts/domains/finance.yaml
- **Related Semantic Model:** semantic_models/domains/finance/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Control cash and liquidity by monitoring balances, operating cash flow, and working capital drivers (DSO, DIO, DPO, CCC).  
**Business Value:** Better liquidity visibility, reduced financing needs, faster cash conversion, and improved resilience.  
**Out of Scope:** Credit risk scoring (COR-016); investment/CapEx tracking (COR-009); supply chain OTIF specifics (SCM-002).

---

## 2. Core Business Questions

- What is the cash position vs plan and how is OCF trending?
- How do DSO, DIO, DPO and CCC develop by region/entity?
- Which customers/suppliers drive cash conversion issues?
- What actions improve cash quickly with minimal business risk?

**Example Query Patterns (optional):**

- "Which regions/entities have CCC above target and DSO deteriorating?"  
- "Where is OCF below plan driven by working capital movements?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: fin.cash.balance
    name: Cash Balance
    purpose: Liquidity level
    definition_short: Cash and cash equivalents
    unit: EUR
    grain: day
    agg: sum
    target: Meet/beat plan and minimum liquidity buffer
    interpretation: Low balance signals liquidity risk
    lineage: fact_cash[Cash Balance]

  - id: fin.cash.ocf
    name: Operating Cash Flow
    purpose: Cash generation
    definition_short: Cash from operating activities
    unit: EUR
    grain: month
    agg: sum
    target: Meet/beat plan
    interpretation: Negative or below plan signals cash pressure
    lineage: fact_cashflow[OCF]

  - id: fin.cash.vs_plan.pct
    name: Cash vs Plan %
    purpose: Performance vs plan
    definition_short: (Cash - Plan) / Plan
    unit: %
    grain: month
    agg: avg
    target: = 0
    interpretation: Negative variance shows liquidity shortfall vs plan
    lineage: fact_cash[Cash], plan_cash

  - id: wc.ccc.days
    name: Cash Conversion Cycle (days)
    purpose: Working capital cycle
    definition_short: DSO + DIO - DPO
    unit: days
    grain: month
    agg: avg
    target: Reduce to target
    interpretation: Higher CCC means slower cash conversion
    lineage: DSO/DIO/DPO measures

  - id: wc.dso.days
    name: DSO (days)
    purpose: Receivables efficiency
    definition_short: AR / (Revenue/365)
    unit: days
    grain: month
    agg: avg
    target: Reduce to target
    interpretation: High DSO slows cash collection
    lineage: fact_ar[AR], revenue

  - id: wc.dio.days
    name: DIO (days)
    purpose: Inventory efficiency
    definition_short: Inventory / (COGS/365)
    unit: days
    grain: month
    agg: avg
    target: Reduce to target
    interpretation: High DIO ties up cash
    lineage: fact_inventory[Inventory], COGS

  - id: wc.dpo.days
    name: DPO (days)
    purpose: Payables efficiency
    definition_short: AP / (COGS/365)
    unit: days
    grain: month
    agg: avg
    target: Optimise vs terms and risk
    interpretation: Higher DPO improves cash, but watch supplier risk
    lineage: fact_ap[AP], COGS
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag cash vs plan negative and OCF below plan.
- Flag CCC above target or deteriorating; drill DSO/DIO/DPO.
- Highlight entities/regions with high DSO or DIO and low DPO.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: fin.cash.vs_plan.pct
    condition: <
    threshold: 0
    scope: entity_region
    exclusion: none
    action_code: W1

  - kpi: wc.ccc.days
    condition: >
    threshold: ccc_target
    scope: entity_region
    exclusion: none
    action_code: W1

  - kpi: wc.dso.days
    condition: >
    threshold: dso_target
    scope: entity_region
    exclusion: disputed_receivables
    action_code: C1

  - kpi: wc.dio.days
    condition: >
    threshold: dio_target
    scope: entity_region
    exclusion: strategic_stock
    action_code: I1

  - kpi: wc.dpo.days
    condition: <
    threshold: dpo_floor
    scope: entity_region
    exclusion: strict_terms
    action_code: W1
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| W1 | Working Capital Improvement | fin.cash.vs_plan.pct < 0 OR CCC > target | Drive AR/Inventory/AP actions to improve CCC | Improve cash vs plan, reduce CCC | L2 | Finance / Ops |
| C1 | Collections Acceleration | wc.dso.days > target | Accelerate collections, reduce disputes, enforce terms | Reduce DSO, improve cash | L2 | Credit/Collections |
| I1 | Inventory Rightsizing | wc.dio.days > target | Reduce inventory, improve replenishment, liquidation | Reduce DIO, improve CCC | L2 | Supply/Inventory |
| W2 | Payables Optimisation | wc.dpo.days < floor | Negotiate terms, extend where feasible | Improve DPO, CCC | L2 | Procurement/AP |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Cash Balance  
- Cash vs Plan %  
- OCF  
- CCC (days)  
- DSO / DIO / DPO  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Cash vs Plan Trend | Line | dim_date[Month] | [Cash], [Plan Cash] | Region/Entity | L12M | Liquidity view |
| CCC vs Target by Entity | Column | dim_org[Entity] | [CCC], [Target] | Region | Current quarter | Decompose CCC |
| DSO/DIO/DPO by Region | Column clustered | dim_org[Region] | [DSO], [DIO], [DPO] | Entity | Current quarter | Driver view |
| OCF vs Plan | Column | dim_date[Month] | [OCF], [Plan OCF] | Region | L12M | Cash generation |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Entity  
- Customer / Supplier (for drill)  
- Product/Category (optional, for DIO)

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

```yaml
required_facts:

  - fact_cash

  - fact_cashflow

  - fact_ar

  - fact_ap

  - fact_inventory (for DIO)

  - fact_cogs (or sales/COGS for rates)
required_dimensions:

  - dim_date

  - dim_org (entity/region)

  - dim_customer (for AR/DSO drill)

  - dim_supplier (for AP/DPO drill)

  - dim_product (for DIO drill)

  - security_user_org
required_grain: day for cash; month for WC metrics; customer/supplier drill for DSO/DPO; location_sku for DIO
required_time_range: 12-24 months history + plan
required_slicers: Date, Region/Entity, Customer/Supplier, Product (optional)
```

---

## 8. Dependencies, Assumptions & Constraints

- Plan and actual cash/OCF available; WC components aligned to same period/entity.
- AR/AP aging available; disputed receivables flagged; strategic stock flagged.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; currency EUR.

---

## 9. Success Criteria

- Impact: Positive cash vs plan; CCC reduced toward target; DSO/DIO down and DPO optimized.  
- Adoption: Used in monthly treasury/WC reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across finance and supply chain; reconciled to source totals.  
- Decision Frequency: Monthly and weekly liquidity reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Misalignment of AR/AP aging with revenue/COGS periods.  
- DIO misread if inventory/COGS not aligned or strategic stock excluded.  
- Overextension of DPO harming supplier relationships.  


