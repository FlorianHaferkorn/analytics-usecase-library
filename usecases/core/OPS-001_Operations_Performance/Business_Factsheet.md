---
id: OPS-001
factsheet_type: business
---

# OPS-001 - Operations Performance  

## Business Factsheet

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-001
- **Domain:** Operations
- **Business Owner:** COO / Plant Manager / Ops Excellence Lead
- **KPI Owner:** Operations Controlling / OEE Lead
- **Decision Owner:** Operations Leadership Team
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Improve overall equipment effectiveness and throughput by addressing availability, performance, and quality losses.  
**Business Value:** Higher OEE, more stable throughput, reduced downtime, and better cost efficiency without additional CAPEX.  
**Out of Scope:** Predictive maintenance specifics (OPS-013); logistics/warehouse performance (OPS-011); detailed cost modeling (OPS-008).

---

## 2. Core Business Questions

- What is OEE and its components (availability, performance, quality) by line/plant?
- Where are the largest downtime and speed losses, and what are the top causes?
- How does throughput vary by shift, line, and product mix?
- Which targeted actions will lift OEE fastest with minimal risk?

**Example Query Patterns (optional):**

- "Which lines have availability < target in the last 4 weeks and what are the top 3 downtime reasons?"
- "Where is performance loss >5% vs standard for top products?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: ops.oee.pct
    kpi_catalog_id: Efficiency
    name: Overall Equipment Effectiveness %
    purpose: Combined availability, performance, quality
    agg: avg

  - id: ops.availability.pct
    name: Availability %
    purpose: Uptime control
    agg: avg

  - id: ops.performance.pct
    name: Performance %
    purpose: Speed vs standard
    agg: avg

  - id: ops.quality.pct
    name: Quality %
    purpose: First pass yield
    agg: avg

  - id: ops.throughput.units
    name: Throughput Units
    purpose: Volume output
    agg: sum

  - id: ops.downtime.pct
    name: Downtime %
    purpose: Unplanned loss
    agg: avg

  - id: ops.planned_output.units
    name: Planned Output Units
    purpose: Plan baseline
    agg: sum
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: O-O1.1
    name: Operations Stabilisation
    purpose: Eliminate Chronic Downtime and Stabilise Operations
    status: active
    owner: Maintenance Manager
    trigger_kpis: [ops.availability.pct, ops.downtime.pct]
    guardrail_kpis: [ops.quality.pct]
    outcome_kpis: [ops.availability.pct, ops.oee.pct]
    impact_range: ops.availability.pct: 3.0-8.0 pp
    levels: L1-L3

  - id: O-O1.2
    name: Performance Uplift
    purpose: Recover Line Speed and Output vs Standard
    status: active
    owner: Production Manager
    trigger_kpis: [ops.performance.pct]
    guardrail_kpis: [ops.availability.pct]
    outcome_kpis: [ops.performance.pct, ops.throughput.units]
    impact_range: ops.performance.pct: 2.0-6.0 pp
    levels: L1-L3

  - id: O-O1.3
    name: Quality & Yield Recovery
    purpose: Stabilise First-Pass Yield and Reduce Scrap
    status: active
    owner: Quality Manager
    trigger_kpis: [ops.quality.pct]
    guardrail_kpis: [ops.availability.pct]
    outcome_kpis: [ops.quality.pct, ops.oee.pct]
    impact_range: ops.quality.pct: 1.0-3.0 pp
    levels: L1-L3

  - id: O-O1.4
    name: Throughput Constraint Resolution
    purpose: Resolve System Constraints Blocking Output
    status: active
    owner: Operations Director
    trigger_kpis: [ops.throughput.units]
    guardrail_kpis: [ops.oee.pct]
    outcome_kpis: [ops.throughput.units]
    impact_range: ops.throughput.units: 3.0-10.0 %
    levels: L1-L3
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- OEE %  
- Availability %  
- Performance %  
- Quality %  
- Downtime %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| OEE vs Target by Line | Column | dim_org[Line] | [OEE %], [Target] | Plant | Current month | Core ranking |
| Downtime by Cause | Bar (horizontal) | fact_ops[Cause] | [Downtime Minutes] | Line/Plant | Last 4 weeks | Pareto |
| Performance Loss vs Standard | Column | dim_org[Line] | [Performance %] | Shift | Last 4 weeks | Speed losses |
| Quality Trend | Line | dim_date[Week] | [Quality %] | Line/Plant | L12W | Stability view |

### 5.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Category (if applicable)  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

```yaml
required_facts:

  - fact_ops (production events/OEE)
required_dimensions:

  - dim_date

  - dim_org (plant/line/shift)

  - dim_product (if needed)

  - security_user_org
required_grain: line_day (or line_shift if available)
required_time_range: 12-24 months history
required_slicers: Date, Plant/Line/Shift, Product (optional)
```

---

## 7. Dependencies, Assumptions & Constraints

- Standard cycle times and planned production time defined; changeovers classified.
- Downtime coded with cause categories; trial runs flagged.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_product optional).
- Data latency =24h; plan vs actual for throughput if used.

---

## 8. Success Criteria

- Impact: OEE uplift toward target; reduced downtime minutes; improved throughput vs plan.  
- Adoption: Used in weekly ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly ops and daily tiered meetings.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime distorts availability.  
- Ignoring product mix/standard rate differences when reading performance %.  
- Quality issues masked if rework/scrap not fully captured.  





