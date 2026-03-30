---
id: FIN-001
factsheet_type: business
---

# FIN-001 - Cash & Liquidity Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** FIN-001
- **Domain:** Finance
- **Business Owner:** CFO / Treasury Lead
- **KPI Owner:** Treasury / Finance Controlling
- **Decision Owner:** Finance Leadership Team
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Predictive
- **Related Data Contract:** core/data_contracts/domains/finance.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Finance.SemanticModel (domain model for FIN-*).

---

## 1. Business Summary

**Purpose:** Control cash and liquidity by monitoring balances, operating cash
flow, and working capital drivers (DSO, DIO, DPO, CCC).  
**Business Value:** Better liquidity visibility, reduced financing needs, faster
cash conversion, and improved resilience.  
**Out of Scope:** Credit risk scoring (COR-016); investment/CapEx tracking
(COR-009); supply chain OTIF specifics (SCM-002).

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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| wc.ccc.days | Strategic |
| fin.cash.balance | Influencing |
| fin.cash.ocf | Influencing |
| fin.cash.vs_plan.pct | Influencing |
| wc.dso.days | Influencing |
| wc.dio.days | Influencing |
| wc.dpo.days | Influencing |
| scm.service_level.pct | Influencing |
| scm.supplier_risk.score | Influencing |
| fin.liquidity.inventory.amount | Supporting |

**Action Codes:** F-C1.1, F-C1.2, S-I1.2, F-C1.4

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Cash Balance  
- Cash vs Plan %  
- OCF  
- CCC (days)  
- DSO / DIO / DPO  

### 5.2 30-Second Layer (Main Visuals)

- **Cash vs Plan Trend**
  - Visual Type: Line
  - X-Axis: dim_date[Month]
  - Y-Axis: [Cash], [Plan Cash]
  - Segment: Region/Entity
  - Default Filter: L12M
  - Notes: Liquidity view

- **CCC vs Target by Entity**
  - Visual Type: Column
  - X-Axis: dim_org[Entity]
  - Y-Axis: [CCC], [Target]
  - Segment: Region
  - Default Filter: Current quarter
  - Notes: Decompose CCC

- **DSO/DIO/DPO by Region**
  - Visual Type: Column clustered
  - X-Axis: dim_org[Region]
  - Y-Axis: [DSO], [DIO], [DPO]
  - Segment: Entity
  - Default Filter: Current quarter
  - Notes: Driver view

- **OCF vs Plan**
  - Visual Type: Column
  - X-Axis: dim_date[Month]
  - Y-Axis: [OCF], [Plan OCF]
  - Segment: Region
  - Default Filter: L12M
  - Notes: Cash generation

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Region / Entity  
- Customer / Supplier (for drill)  
- Product/Category (optional, for DIO)

---

### 5.4 300-Second Layer (Diagnostics)

- AR aging detail by customer and entity: outstanding invoices, days overdue, dispute status.
- AP aging detail by supplier: payment timing vs contracted terms; early payment discount opportunities.
- DIO by SKU/location with coverage days vs safety stock target.
- OCF bridge: EBITDA → operating cash flow with working capital movement waterfall.

## 6. Data Requirements Summary

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
required_grain: >
  day for cash; month for WC metrics; customer/supplier drill for DSO/DPO;
  location_sku for DIO
required_time_range: 12-24 months history + plan
required_slicers: >
  Date, Region/Entity, Customer/Supplier, Product (optional)
```

---

## 7. Dependencies, Assumptions & Constraints

- Plan and actual cash/OCF available; WC components aligned to same
  period/entity.
- AR/AP aging available; disputed receivables flagged; strategic stock flagged.
- OneLake canonical dims used (dim_date, dim_org, dim_product,
  security_user_org).
- Data latency =24h; currency EUR.

---

## 8. Success Criteria

- Impact: Positive cash vs plan; CCC reduced toward target; DSO/DIO down and DPO
  optimized.  
- Adoption: Used in monthly treasury/WC reviews; action codes triggered with <5%
  false positives.  
- Quality: KPI definitions consistent across finance and supply chain;
  reconciled to source totals.  
- Decision Frequency: Monthly and weekly liquidity reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misalignment of AR/AP aging with revenue/COGS periods.
- DIO misread if inventory/COGS not aligned or strategic stock excluded.
- Overextension of DPO harming supplier relationships.

---

## 10. Typical Decision Scenarios

### Scenario A: Cash Below Plan Driven by DSO Deterioration

**Situation:** Cash position is −12% vs plan at month-end. OCF is broadly on track, but CCC has extended by 8 days vs prior quarter, entirely explained by DSO rising from 45 to 53 days. Two large customers in the Western Europe region account for 60% of the outstanding AR increase.

**Decision question:** Is the DSO increase driven by customer payment behavior (structural), by invoice disputes (operational), or by a change in payment terms granted by sales?

**Who decides:** Treasury / Finance Controlling Lead + Credit & Collections Manager.

**Consequence of inaction:** At €150M annual revenue, 8 additional DSO days = ~€3.3M of cash tied up in receivables. Cash covenant risk if trend persists for 2 more months.

**Action Code triggered:** F-C1.1 (DSO Recovery) — activates customer-level AR aging review and collections escalation protocol.

### Scenario B: DIO Spike Following Inventory Build Decision

**Situation:** DIO has risen from 62 to 79 days in the last 2 months. Finance flags as a working capital concern. Supply Chain explains this was an approved strategic buffer for a seasonal peak.

**Decision question:** Is the inventory build within the approved S&OP buffer range, or has it exceeded the approved limit?

**Who decides:** CFO + Supply Chain Controlling Lead.

**Consequence of inaction:** None if within approved policy (this is the `when_not_to_act` scenario for DEC-SPINE-FIN-LIQUIDITY). If outside policy, +€8M inventory carries an annualized cost of capital impact.

**Action Code triggered:** None if within approved buffer. F-K2.2 (DIO Reduction) triggered only if buffer threshold exceeded.

### Scenario C: OCF Below Plan Despite Positive EBITDA

**Situation:** EBITDA is +3% vs plan, but OCF is −15% vs plan. The bridge analysis shows that working capital consumed €8M more cash than planned, primarily from AR increase (+€5M) and inventory build (+€3M).

**Decision question:** Is the OCF gap temporary (timing) or structural? Which lever (DSO, DIO, or DPO) offers fastest recovery with lowest business risk?

**Who decides:** CFO-sponsored working capital review (DEC-SPINE-FIN-LIQUIDITY, RequiredIntervention level).

**Consequence of inaction:** Positive EBITDA will be misread as financial health. Liquidity risk can materialize within 60–90 days if not addressed.

**Action Code triggered:** F-C1.1 and/or F-K2.2 depending on root cause of bridge analysis.

---



