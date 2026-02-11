---
id: OPS-003
factsheet_type: business
---

# OPS-003 - Quality & Yield  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-003
- **Domain:** Operations
- **Business Owner:** COO / Head of Quality
- **KPI Owner:** Quality Manager / Ops Controlling
- **Decision Owner:** Operations & Quality Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** core/core/core/data_contracts/domains/operations.yaml
- **Related Semantic Model:** core/core/core/semantic_models/core_action_ready/model_definition.yaml

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
    kpi_catalog_id: Efficiency
    name: First Pass Yield %
    purpose: Process quality
    agg: avg

  - id: quality.scrap.pct
    name: Scrap Rate %
    purpose: Waste reduction
    agg: avg

  - id: quality.rework.pct
    name: Rework Rate %
    purpose: Rework burden
    agg: avg

  - id: quality.copq.amount
    name: Cost of Poor Quality (COPQ)
    purpose: Financial impact
    agg: sum

  - id: quality.complaint.pct
    name: Complaint Rate %
    purpose: Customer impact
    agg: avg

  - id: quality.defect_density
    name: Defect Density
    purpose: Defect concentration
    agg: avg

  - id: ops.planned_output.units
    name: Planned Output Units
    purpose: Volume baseline
    agg: sum

  - id: sales.units
    name: Sales Units
    purpose: Demand context
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: O-Q3.1
    name: Quality & Yield Orchestration
    purpose: Coordinate Quality and Yield Improvement Actions
    status: active
    owner: Head of Quality
    trigger_kpis: [quality.fpy.pct, quality.scrap.pct]
    guardrail_kpis: [ops.throughput.units]
    outcome_kpis: [quality.fpy.pct]
    impact_range: quality.fpy.pct: 1.0-3.0 pp
    levels: L1-L3

  - id: O-Q3.2
    name: Process Defect Elimination
    purpose: Eliminate Dominant Process Defects
    status: active
    owner: Quality Engineer
    trigger_kpis: [quality.defect_density]
    guardrail_kpis: [ops.availability.pct]
    outcome_kpis: [quality.defect_density, quality.fpy.pct]
    impact_range: quality.defect_density: -20.0--50.0 %
    levels: L1-L3

  - id: O-Q3.3
    name: Scrap & Rework Reduction
    purpose: Reduce Internal Scrap and Rework Loops
    status: active
    owner: Production Manager
    trigger_kpis: [quality.scrap.pct, quality.rework.pct]
    guardrail_kpis: [quality.fpy.pct]
    outcome_kpis: [quality.scrap.pct, quality.rework.pct]
    impact_range: quality.scrap.pct: -0.5--2.0 pp
    levels: L1-L3

  - id: O-Q3.4
    name: COPQ Reduction
    purpose: Eliminate Financially Material Quality Losses
    status: active
    owner: Head of Quality
    trigger_kpis: [quality.copq.amount]
    guardrail_kpis: [quality.fpy.pct]
    outcome_kpis: [quality.copq.amount]
    impact_range: quality.copq.amount: -10.0--30.0 %
    levels: L1-L3

  - id: O-Q3.5
    name: Complaint-Driven Stabilisation
    purpose: Stabilise Processes Driving Customer Complaints
    status: active
    owner: Quality Manager
    trigger_kpis: [quality.complaint.pct]
    guardrail_kpis: [quality.fpy.pct]
    outcome_kpis: [quality.complaint.pct]
    impact_range: quality.complaint.pct: -20.0--50.0 %
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- First Pass Yield %  
- Scrap Rate %  
- Rework Rate %  
- COPQ (EUR)  
- Complaint Rate %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| FPY vs Target by Line | Column | dim_org[Line] | [FPY %], [Target] | Plant | Current month | Core ranking |
| Scrap & Rework Trend | Line | dim_date[Week] | [Scrap %], [Rework %] | Line/Plant | L12W | Stability |
| COPQ by Cause/Product | Bar (horizontal) | fact_quality_costs[Cause/Product] | [COPQ] | Line/Plant | Last quarter | Pareto |
| Complaint Rate vs FPY | Scatter | [FPY %] | [Complaint %] | Product Family | Current quarter | Field impact |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Product Family  
- Defect Type / Cause  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

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

## 7. Dependencies, Assumptions & Constraints

- Defect and cause coding available; scrap/rework measured at line/product level.
- Complaint data linked to product and period; shipments available.
- COPQ captures scrap, rework, warranty/complaint costs.
- OneLake canonical dims used (dim_date, dim_org, dim_product, security_user_org).

---

## 8. Success Criteria

- Impact: FPY improves to targets; scrap/rework reduced; COPQ reduced; complaint rate lowered.  
- Adoption: Used in weekly quality/ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; reconciled units with production totals.  
- Decision Frequency: Weekly and monthly quality review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misattributing scrap to wrong cause/product due to coding gaps.  
- Understating complaint rate if shipment linkage is weak.  
- Overreacting to short-term FPY dips without considering planned trials.  





