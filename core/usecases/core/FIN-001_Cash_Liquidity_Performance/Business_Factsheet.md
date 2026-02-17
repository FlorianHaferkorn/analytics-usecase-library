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
- **Related Semantic Model:** core/semantic_models/core_action_ready/model_definition.yaml

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

- (optional)

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



