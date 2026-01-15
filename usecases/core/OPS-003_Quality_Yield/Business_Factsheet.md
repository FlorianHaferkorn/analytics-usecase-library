---
id: OPS-003
factsheet_type: business
---

# OPS-003 - Quality & Yield  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-003
- **Domain:** Operations
- **Business Owner:** COO / Head of Quality
- **KPI Owner:** Quality Manager / Ops Controlling
- **Decision Owner:** Operations & Quality Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Improve first pass yield and reduce scrap/rework by identifying top defect drivers and cost of poor quality.  
**Business Value:** Higher yield, lower scrap/rework cost, fewer customer complaints, more stable throughput and margin.  
**Out of Scope:** Supplier PPV and compliance (OPS-002 scope); predictive maintenance (OPS-013); logistics quality (OPS-011).

---

## 2. Core Business Questions

- What is FPY and scrap/rework performance by line, product, and shift?
- Which defect types and steps drive the most quality losses and COPQ?
- How do complaints correlate with plant/line/product performance?
- Which actions reduce defects fastest with minimal throughput impact?

**Example Query Patterns (optional):**

- "Which lines have FPY below target and scrap > target in the last 4 weeks?"
- "What are the top 5 defect causes by cost for product family X?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: quality.fpy.pct
    name: First Pass Yield %
    purpose: Process quality
    definition_short: Good units / Total units at first pass
    unit: %
    grain: line_day
    agg: avg
    target: = site/line target (e.g., 98%+)
    interpretation: Low FPY indicates rework/scrap issues
    lineage: fact_quality[Good Units], fact_quality[Total Units]

  - id: quality.scrap.pct
    name: Scrap Rate %
    purpose: Waste reduction
    definition_short: Scrap units / Total units
    unit: %
    grain: line_day
    agg: avg
    target: = target (e.g., <2%)
    interpretation: High scrap signals process defects
    lineage: fact_quality[Scrap Units], fact_quality[Total Units]

  - id: quality.rework.pct
    name: Rework Rate %
    purpose: Rework burden
    definition_short: Reworked units / Total units
    unit: %
    grain: line_day
    agg: avg
    target: = target
    interpretation: High rework inflates cost and reduces capacity
    lineage: fact_quality[Rework Units], fact_quality[Total Units]

  - id: quality.copq.amount
    name: Cost of Poor Quality (COPQ)
    purpose: Financial impact
    definition_short: Scrap + rework + warranty/complaint cost
    unit: EUR
    grain: month
    agg: sum
    target: Reduce vs baseline
    interpretation: High COPQ signals material loss and customer risk
    lineage: fact_quality_costs[COPQ], fact_quality

  - id: quality.complaint.pct
    name: Complaint Rate %
    purpose: Customer impact
    definition_short: Complaints / Units shipped
    unit: %
    grain: month
    agg: avg
    target: = target
    interpretation: High complaints indicate field quality issues
    lineage: fact_complaints[Complaints], fact_shipments[Units]

  - id: quality.defect_density
    name: Defect Density
    purpose: Defect concentration
    definition_short: Defects per 1k units
    unit: defects/1k units
    grain: line_day
    agg: avg
    target: = target
    interpretation: High density signals process stability issues
    lineage: fact_quality[Defect Count], fact_quality[Units]

  - id: ops.planned_output.units
    name: Planned Output Units
    purpose: Volume baseline
    definition_short: Planned production output units
    unit: units
    grain: line_day
    agg: sum
    target: Meet plan
    interpretation: Planned volume for yield context
    lineage: fact_ops[Planned Output Units]

  - id: sales.units
    name: Sales Units
    purpose: Demand context
    definition_short: Units sold in the period
    unit: units
    grain: month
    agg: sum
    target: Meet plan
    interpretation: Demand context for quality impact
    lineage: fact_sales[Sales Units]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag FPY below target or scrap/rework above threshold for 2 consecutive periods.
- Escalate defect density hotspots and top COPQ contributors.
- Flag rising complaint rate correlated with specific lines/products.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: quality.fpy.pct
    condition: <
    threshold: line_target
    scope: line_week
    exclusion: ramp-up runs
    action_code: L2

  - kpi: quality.scrap.pct
    condition: >
    threshold: 0.02
    scope: line_week
    exclusion: trial_runs
    action_code: L2

  - kpi: quality.copq.amount
    condition: >
    threshold: copq_materiality
    scope: product_family
    exclusion: none
    action_code: D1

  - kpi: quality.complaint.pct
    condition: >
    threshold: target
    scope: product_family
    exclusion: none
    action_code: O2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| L2 | Quality & Yield | FPY below target or scrap/rework above threshold | Fix defect causes, tighten process controls, adjust parameters | Improve FPY, reduce scrap/rework | L2 | Quality / Production |
| O2 | Operations Stabilisation | Complaint rate high linked to process instability | Stabilise process, address variation | Reduce complaints, improve FPY | L2 | Ops Excellence |
| D1 | Cost Take-Out / COPQ Reduction | COPQ above materiality | Remove waste, improve supplier/material/process controls | Reduce COPQ, scrap | L2 | Quality / Procurement |
| M2 | Performance Uplift | Performance loss tied to rework loops | Reduce rework loops to free capacity | Improve performance, FPY | L2 | Production |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- First Pass Yield %  
- Scrap Rate %  
- Rework Rate %  
- COPQ (EUR)  
- Complaint Rate %  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| FPY vs Target by Line | Column | dim_org[Line] | [FPY %], [Target] | Plant | Current month | Core ranking |
| Scrap & Rework Trend | Line | dim_date[Week] | [Scrap %], [Rework %] | Line/Plant | L12W | Stability |
| COPQ by Cause/Product | Bar (horizontal) | fact_quality_costs[Cause/Product] | [COPQ] | Line/Plant | Last quarter | Pareto |
| Complaint Rate vs FPY | Scatter | [FPY %] | [Complaint %] | Product Family | Current quarter | Field impact |

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Product Family  
- Defect Type / Cause  

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

```yaml
required_facts:

  - fact_quality (units, good, scrap, rework, defects)

  - fact_quality_costs (COPQ)

  - fact_complaints (field complaints)

  - fact_shipments (for complaint rate)
required_dimensions:

  - dim_date

  - dim_org (plant/line/shift)

  - dim_product

  - security_user_org
required_grain: line_day for quality; complaint_month for complaints
required_time_range: 12-24 months history
required_slicers: Date, Plant/Line/Shift, Product, Defect Type
```

---

## 8. Dependencies, Assumptions & Constraints

- Defect and cause coding available; scrap/rework measured at line/product level.
- Complaint data linked to product and period; shipments available.
- COPQ captures scrap, rework, warranty/complaint costs.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 9. Success Criteria

- Impact: FPY improves to targets; scrap/rework reduced; COPQ reduced; complaint rate lowered.  
- Adoption: Used in weekly quality/ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; reconciled units with production totals.  
- Decision Frequency: Weekly and monthly quality review.

---

## 10. Risks & Wrong Interpretations (Short)

- Misattributing scrap to wrong cause/product due to coding gaps.  
- Understating complaint rate if shipment linkage is weak.  
- Overreacting to short-term FPY dips without considering planned trials.  


