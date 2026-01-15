---
id: FIN-002
factsheet_type: business
---

# FIN-002 - Cost Performance  

## Business Factsheet (v1.2)

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
    name: Unit Cost Amount
    purpose: Cost efficiency
    definition_short: Total COGS / Units produced or sold
    unit: EUR/unit
    grain: product_line_month
    agg: avg
    target: = plan target
    interpretation: Higher than plan signals cost pressure
    lineage: fact_cost[COGS], fact_output[Units]

  - id: margin.cogs.pct
    name: COGS % of Sales
    purpose: Cost share
    definition_short: COGS / Net Sales
    unit: %
    grain: month
    agg: avg
    target: = target
    interpretation: Rising % erodes margin
    lineage: fact_finance[COGS], fact_finance[Net Sales]

  - id: cost.opex.vs_plan.pct
    name: OpEx vs Plan %
    purpose: Overhead control
    definition_short: (OpEx - Plan) / Plan
    unit: %
    grain: month
    agg: avg
    target: = 0
    interpretation: Positive variance indicates overspend
    lineage: fact_opex[OpEx], plan_opex

  - id: cost.material.pct
    name: Material Cost %
    purpose: Material efficiency
    definition_short: Material cost / Net Sales
    unit: %
    grain: month
    agg: avg
    target: = target
    interpretation: High material share signals price/usage issues
    lineage: fact_cost[Material Cost], fact_finance[Net Sales]

  - id: ops.labor.productivity.pct
    name: Labor Productivity %
    purpose: Labor efficiency
    definition_short: Output vs labor hours (or revenue per labor hour)
    unit: index/%
    grain: month
    agg: avg
    target: = target
    interpretation: Low productivity increases unit cost
    lineage: fact_output[Units], fact_labor[Labor Hours]

  - id: cost.base_volume.amount
    name: Cost Base Volume Amount
    purpose: Variance baseline
    definition_short: Baseline cost volume amount
    unit: EUR
    grain: cost_center_month
    agg: sum
    target: = baseline
    interpretation: Baseline for cost variance comparisons
    lineage: fact_cost[Base Volume Amount]

  - id: cost.opex.base.amount
    name: Opex Base Amount
    purpose: OpEx baseline
    definition_short: Baseline operating expense amount
    unit: EUR
    grain: cost_center_month
    agg: sum
    target: = baseline
    interpretation: Baseline for OpEx variance tracking
    lineage: fact_opex[Opex Base Amount]

  - id: ops.production.volume
    name: Production Volume Units
    purpose: Output baseline
    definition_short: Total produced units
    unit: units
    grain: line_month
    agg: sum
    target: Meet plan
    interpretation: Volume context for unit cost movements
    lineage: fact_ops[Output Units]

  - id: ops.quality.defect_rate.pct
    name: Quality Defect Rate %
    purpose: Quality cost driver
    definition_short: Defect Units / Output Units
    unit: %
    grain: line_month
    agg: avg
    target: <= target
    interpretation: Higher defect rates raise rework and unit cost
    lineage: fact_quality[Defect Count], fact_ops[Output Units]

  - id: ops.service_level.pct
    name: Operations Service Level %
    purpose: Service guardrail
    definition_short: On-Time Deliveries / Total Deliveries
    unit: %
    grain: shipment_month
    agg: avg
    target: >= service target
    interpretation: Cost actions should not reduce service
    lineage: fact_ops[On Time Deliveries], fact_ops[Total Deliveries]

  - id: ops.yield.pct
    name: Yield %
    purpose: Process efficiency
    definition_short: Good Units / Output Units
    unit: %
    grain: line_month
    agg: avg
    target: >= target
    interpretation: Low yield increases scrap and unit cost
    lineage: fact_ops[Good Units], fact_ops[Output Units]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action codes.

### 4.1 Logic Description

- Flag unit cost above plan and margin/COGS % off target.
- Flag material cost % above target; investigate mix/price/usage.
- Flag labor productivity below target.
- Flag OpEx variance above 0 for 2 consecutive periods.

### 4.2 Formal Action Code Rules (Machine-Readable)

```yaml
action_codes:

  - kpi: cost.unit.amount
    condition: >
    threshold: plan_target
    scope: plant_line_product
    exclusion: ramp-up runs
    action_code: F-K2.1

  - kpi: cost.material.pct
    condition: >
    threshold: material_target
    scope: plant_line_product
    exclusion: launch_items
    action_code: F-K2.2

  - kpi: ops.labor.productivity.pct
    condition: <
    threshold: productivity_target
    scope: plant_line
    exclusion: training_periods
    action_code: F-K2.3

  - kpi: cost.opex.vs_plan.pct
    condition: >
    threshold: 0
    scope: entity
    exclusion: approved_variances
    action_code: F-K2.1
```

---

## 5. Action Codes (Mandatory)

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| F-K2.1 | Cost Take-Out Orchestration | cost.opex.vs_plan.pct > 0; cost.unit.amount > plan_target | Select dominant cost lever to activate (Material, Labor, OpEx); Sequence cost actions to avoid overlap and conflict | cost.unit.amount +2.0-6.0 % (1-3 periods) | L1 | Finance / Operations |
| F-K2.2 | Material Cost Discipline | cost.material.pct > material_target | Tighten material usage and scrap control; Activate sourcing and spec-discipline corrections | cost.material.pct +1.0-4.0 % (2-4 periods) | L2 | Procurement / Operations |
| F-K2.3 | Labor Productivity Recovery | ops.labor.productivity.pct < productivity_target | Correct staffing and shift imbalances; Stabilize line productivity and utilization | ops.labor.productivity.pct +3.0-8.0 pp (1-3 periods) | L2 | Operations / Production |

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Unit Cost Amount  
- COGS % of Sales  
- OpEx vs Plan %  
- Material Cost %  
- Labor Productivity %  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Unit Cost vs Plan by Plant/Line | Column | dim_org[Plant/Line] | [Unit Cost], [Plan] | Product | Current quarter | Core ranking |
| COGS % vs Target | Column | dim_org[Entity] | [COGS %], [Target] | Region | Current quarter | Margin driver |
| Material Cost % Trend | Line | dim_date[Month] | [Material Cost %] | Plant/Category | L12M | Efficiency trend |
| OpEx vs Plan | Column | dim_org[Entity] | [OpEx vs Plan %] | Region | Current quarter | Overhead control |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Entity / Plant / Line  
- Product / Category  
- Cost bucket (Material/Labor/OpEx)

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- Plan vs actual available for unit cost and OpEx; cost buckets aligned to same period.
- Allocation rules for overhead clear; labor hours available; material costs separated.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).
- Data latency =24h; currency EUR.

---

## 9. Success Criteria

- Impact: Reduced unit cost vs plan; improved COGS %; material cost % lowered; productivity improved.  
- Adoption: Used in monthly ops/finance reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across finance/ops; reconciled to source totals.  
- Decision Frequency: Monthly and weekly cost reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Misallocation of overhead distorting unit cost.  
- Material cost % misread if price/volume/mix effects not separated.  
- Productivity dips during planned training/ramp-up misinterpreted.  


