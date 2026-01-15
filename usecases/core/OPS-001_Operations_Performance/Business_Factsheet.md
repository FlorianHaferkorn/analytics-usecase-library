---
id: OPS-001
factsheet_type: business
---

# OPS-001 - Operations Performance  

## Business Factsheet (v1.2)

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
    name: Overall Equipment Effectiveness %
    purpose: Combined availability, performance, quality
    definition_short: Availability % x Performance % x Quality %
    unit: %
    grain: line_day
    agg: avg
    target: = site/line target (e.g., 85%+)
    interpretation: Core effectiveness; low values indicate combined losses
    lineage: fact_ops[Availability %], fact_ops[Performance %], fact_ops[Quality %]

  - id: ops.availability.pct
    name: Availability %
    purpose: Uptime control
    definition_short: Run Time / Planned Production Time
    unit: %
    grain: line_day
    agg: avg
    target: = 90% (context-specific)
    interpretation: Low availability signals downtime issues
    lineage: fact_ops[Run Time], fact_ops[Planned Time]

  - id: ops.performance.pct
    name: Performance %
    purpose: Speed vs standard
    definition_short: Actual Output / Theoretical Output at standard rate
    unit: %
    grain: line_day
    agg: avg
    target: = 95% (context-specific)
    interpretation: Low performance shows speed losses
    lineage: fact_ops[Output], standards

  - id: ops.quality.pct
    name: Quality %
    purpose: First pass yield
    definition_short: Good Units / Total Units
    unit: %
    grain: line_day
    agg: avg
    target: = 98% (context-specific)
    interpretation: Low quality shows scrap/rework issues
    lineage: fact_ops[Good Units], fact_ops[Total Units]

  - id: ops.throughput.units
    name: Throughput Units
    purpose: Volume output
    definition_short: Units produced over time
    unit: qty
    grain: line_day
    agg: sum
    target: Meet plan
    interpretation: Volume realization vs plan
    lineage: fact_ops[Produced Units]

  - id: ops.downtime.pct
    name: Downtime %
    purpose: Unplanned loss
    definition_short: Downtime / Planned Production Time
    unit: %
    grain: line_day
    agg: avg
    target: = target (e.g., <5%)
    interpretation: High downtime reduces availability
    lineage: fact_ops[Downtime], fact_ops[Planned Time]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag lines with OEE below target or availability/performance/quality below thresholds.
- Escalate chronic downtime causes exceeding target minutes per week.
- Highlight lines with throughput shortfall vs plan and correlated performance loss.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: ops.oee.pct
    condition: <
    threshold: line_target
    scope: line_week
    exclusion: ramp-up lines
    action_code: O2

  - kpi: ops.availability.pct
    condition: <
    threshold: 0.9
    scope: line_week
    exclusion: planned_shutdowns
    action_code: O2

  - kpi: ops.performance.pct
    condition: <
    threshold: 0.95
    scope: line_week
    exclusion: changeover windows
    action_code: M2

  - kpi: ops.quality.pct
    condition: <
    threshold: 0.98
    scope: line_week
    exclusion: trial_runs
    action_code: L2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| O2 | Operations Stabilisation | ops.oee.pct < target OR availability < 90% | Address top downtime causes, standardise maintenance | Improve OEE, availability | L2 | Ops Excellence / Maintenance |
| M2 | Performance Uplift | ops.performance.pct < 95% | Fix speed losses, optimize setups, balance lines | Improve performance %, throughput | L2 | Production |
| L2 | Quality & Yield | ops.quality.pct < 98% | Reduce scrap/rework, tighten process control | Improve quality %, reduce waste | L2 | Quality / Production |
| D1 | Cost Take-Out / COGS Control | cost-driven losses | Address cost of downtime/inefficiency | Reduce loss, improve OEE impact | L2 | Ops / Finance |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- OEE %  
- Availability %  
- Performance %  
- Quality %  
- Downtime %  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| OEE vs Target by Line | Column | dim_org[Line] | [OEE %], [Target] | Plant | Current month | Core ranking |
| Downtime by Cause | Bar (horizontal) | fact_ops[Cause] | [Downtime Minutes] | Line/Plant | Last 4 weeks | Pareto |
| Performance Loss vs Standard | Column | dim_org[Line] | [Performance %] | Shift | Last 4 weeks | Speed losses |
| Quality Trend | Line | dim_date[Week] | [Quality %] | Line/Plant | L12W | Stability view |

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Plant / Line / Shift  
- Product / Category (if applicable)  

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

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

## 8. Dependencies, Assumptions & Constraints

- Standard cycle times and planned production time defined; changeovers classified.
- Downtime coded with cause categories; trial runs flagged.
- OneLake canonical dims used (dim_date, dim_org, security_user_org; dim_product optional).
- Data latency =24h; plan vs actual for throughput if used.

---

## 9. Success Criteria

- Impact: OEE uplift toward target; reduced downtime minutes; improved throughput vs plan.  
- Adoption: Used in weekly ops reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly ops and daily tiered meetings.

---

## 10. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime distorts availability.  
- Ignoring product mix/standard rate differences when reading performance %.  
- Quality issues masked if rework/scrap not fully captured.  


