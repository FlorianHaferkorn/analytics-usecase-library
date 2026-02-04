---
id: FIN-002
factsheet_type: business
---

# FIN-002 - Cost Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** FIN-002
- **Domain:** Finance / Operations
- **Business Owner:** CFO / Ops Finance Lead
- **KPI Owner:** Plant/Ops Controllers
- **Decision Owner:** Finance & Operations Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/finance.yaml
- **Related Semantic Model:** semantic_models/domains/finance/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Reduce unit cost and improve margin by controlling material, labor, and OpEx vs plan.  
**Business Value:** Better cost competitiveness, margin protection, and more efficient operations without sacrificing throughput/quality.  
**Out of Scope:** Detailed OEE/performance tuning (OPS-001); supplier PPV specifics (OPS-002); logistics cost ratio (OPS-009).

---

## 2. Core Business Questions

- What is unit cost vs plan/LY by plant/line/product?
- Which cost buckets (material, labor, overhead/OpEx) drive variance?
- Where is COGS % rising and margin eroding?
- Which actions reduce cost fastest without harming service/quality?

**Example Query Patterns (optional):**

- "Which plants have unit cost above plan and margin below target in the last quarter?"
- "Which products show highest material cost % variance?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: cost.unit.amount
    kpi_catalog_id: Profitability
    name: Unit Cost Amount
    purpose: Cost efficiency
    agg: avg

  - id: margin.cogs.pct
    name: COGS % of Sales
    purpose: Cost share
    agg: avg

  - id: cost.opex.vs_plan.pct
    name: OpEx vs Plan %
    purpose: Overhead control
    agg: avg

  - id: cost.material.pct
    name: Material Cost %
    purpose: Material efficiency
    agg: avg

  - id: ops.labor.productivity.pct
    name: Labor Productivity %
    purpose: Labor efficiency
    agg: avg

  - id: cost.base_volume.amount
    name: Cost Base Volume Amount
    purpose: Variance baseline
    agg: sum

  - id: cost.opex.base.amount
    name: Opex Base Amount
    purpose: OpEx baseline
    agg: sum

  - id: ops.production.volume
    name: Production Volume Units
    purpose: Output baseline
    agg: sum

  - id: ops.quality.defect_rate.pct
    name: Quality Defect Rate %
    purpose: Quality cost driver
    agg: avg

  - id: ops.service_level.pct
    name: Operations Service Level %
    purpose: Service guardrail
    agg: avg

  - id: ops.yield.pct
    name: Yield %
    purpose: Process efficiency
    agg: avg
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: F-K2.1
    name: Cost Take-Out Orchestration
    purpose: Integrated Cost Take-Out Control
    status: active
    owner: Finance Director
    trigger_kpis: [cost.unit.amount, cost.opex.vs_plan.pct]
    guardrail_kpis: [ops.labor.productivity.pct]
    outcome_kpis: [cost.unit.amount]
    impact_range: cost.unit.amount: 2.0-6.0 %
    levels: L1-L3

  - id: F-K2.2
    name: Material Cost Discipline
    purpose: Stabilize and Reduce Material Cost per Unit
    status: active
    owner: Head of Procurement
    trigger_kpis: [cost.material.pct]
    guardrail_kpis: [ops.yield.pct]
    outcome_kpis: [cost.material.pct, cost.unit.amount]
    impact_range: cost.material.pct: 1.0-4.0 %
    levels: L1-L3

  - id: F-K2.3
    name: Labor Productivity Recovery
    purpose: Recover Productivity to Reduce Unit Cost
    status: active
    owner: Plant Manager
    trigger_kpis: [ops.labor.productivity.pct]
    guardrail_kpis: [ops.quality.defect_rate.pct]
    outcome_kpis: [ops.labor.productivity.pct, cost.unit.amount]
    impact_range: ops.labor.productivity.pct: 3.0-8.0 pp
    levels: L1-L3

  - id: F-K2.4
    name: OpEx Discipline
    purpose: Protect Margin via OpEx Discipline
    status: active
    owner: Head of Controlling
    trigger_kpis: [cost.opex.vs_plan.pct]
    guardrail_kpis: [ops.service_level.pct]
    outcome_kpis: [cost.opex.vs_plan.pct, cost.unit.amount]
    impact_range: cost.opex.vs_plan.pct: 2.0-6.0 pp
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Unit Cost Amount  
- COGS % of Sales  
- OpEx vs Plan %  
- Material Cost %  
- Labor Productivity %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Unit Cost vs Plan by Plant/Line | Column | dim_org[Plant/Line] | [Unit Cost], [Plan] | Product | Current quarter | Core ranking |
| COGS % vs Target | Column | dim_org[Entity] | [COGS %], [Target] | Region | Current quarter | Margin driver |
| Material Cost % Trend | Line | dim_date[Month] | [Material Cost %] | Plant/Category | L12M | Efficiency trend |
| OpEx vs Plan | Column | dim_org[Entity] | [OpEx vs Plan %] | Region | Current quarter | Overhead control |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Entity / Plant / Line  
- Product / Category  
- Cost bucket (Material/Labor/OpEx)

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_cost (COGS, material)

  - fact_output (units)

  - fact_finance (Net Sales/COGS for COGS %)

  - fact_opex (OpEx vs Plan)

  - fact_labor (labor hours/productivity)
required_dimensions:

  - dim_date

  - dim_org (entity/plant/line)

  - dim_product

  - security_user_org
required_grain: plant_line_product_month for unit cost; month/entity for OpEx
required_time_range: 12-24 months history + plan
required_slicers: Date, Entity/Plant/Line, Product/Category, Cost bucket
```

---

## 7. Dependencies, Assumptions & Constraints

- Plan vs actual available for unit cost and OpEx; cost buckets aligned to same period.
- Allocation rules for overhead clear; labor hours available; material costs separated.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; currency EUR.

---

## 8. Success Criteria

- Impact: Reduced unit cost vs plan; improved COGS %; material cost % lowered; productivity improved.  
- Adoption: Used in monthly ops/finance reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across finance/ops; reconciled to source totals.  
- Decision Frequency: Monthly and weekly cost reviews.

---

## 9. Risks & Wrong Interpretations (Short)

- Misallocation of overhead distorting unit cost.  
- Material cost % misread if price/volume/mix effects not separated.  
- Productivity dips during planned training/ramp-up misinterpreted.  





