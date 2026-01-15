---
id: OPS-002
factsheet_type: business
---

# OPS-002 - Asset Performance  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** OPS-002
- **Domain:** Operations
- **Business Owner:** COO / Head of Maintenance / Reliability Engineering Lead
- **KPI Owner:** Maintenance Controlling / Reliability
- **Decision Owner:** Operations & Maintenance Leadership
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Improve asset reliability and availability by reducing unplanned downtime and optimizing preventive maintenance.  
**Business Value:** Higher availability, fewer breakdowns, lower maintenance cost from better PM compliance and spare-part readiness.  
**Out of Scope:** Predictive maintenance algorithms (OPS-013); production throughput optimization (OPS-001); logistics/warehouse (OPS-011).

---

## 2. Core Business Questions

- Which assets/lines have the highest unplanned downtime and what are the root causes?
- How do MTBF/MTTR trend by asset class and site?
- Is preventive maintenance executed on time and effective?
- Where do spare-part stockouts create maintenance risk?
- Which actions reduce downtime fastest with acceptable cost?

**Example Query Patterns (optional):**

- "Which assets have MTBF below target and MTTR above target in the last 90 days?"
- "Where is PM compliance < target and unplanned downtime rising?"

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:

  - id: ops.availability.pct
    name: Availability %
    purpose: Asset uptime
    definition_short: Run Time / Planned Time
    unit: %
    grain: asset_day
    agg: avg
    target: = 90% (context-specific)
    interpretation: Low availability shows downtime issues
    lineage: fact_ops[Run Time], fact_ops[Planned Time]

  - id: ops.mtbf.hours
    name: MTBF (hours)
    purpose: Reliability
    definition_short: Operating time between failures
    unit: hours
    grain: asset
    agg: avg
    target: Asset-class target
    interpretation: Lower than target indicates frequent failures
    lineage: fact_ops_failures[Failure Start/End], uptime calc

  - id: ops.mttr.hours
    name: MTTR (hours)
    purpose: Maintainability
    definition_short: Average repair time per failure
    unit: hours
    grain: asset
    agg: avg
    target: Asset-class target
    interpretation: High MTTR prolongs downtime
    lineage: fact_ops_failures[Repair Duration]

  - id: ops.downtime.unplanned.pct
    name: Unplanned Downtime %
    purpose: Unplanned loss
    definition_short: Unplanned downtime / Planned Time
    unit: %
    grain: asset_day
    agg: avg
    target: = target (e.g., <5%)
    interpretation: High values indicate reliability issues
    lineage: fact_ops[Unplanned Downtime], fact_ops[Planned Time]

  - id: ops.spare_parts.stockout.pct
    name: Spare Parts Stockout %
    purpose: Maintenance readiness
    definition_short: Maintenance orders delayed due to missing parts / total orders
    unit: %
    grain: month
    agg: avg
    target: = target (e.g., <2%)
    interpretation: High stockouts create MTTR risk
    lineage: fact_maintenance[Orders Delayed], fact_maintenance[Orders]

  - id: ops.pm_compliance.pct
    name: PM Compliance %
    purpose: Preventive maintenance discipline
    definition_short: PM orders on time / planned PM orders
    unit: %
    grain: month
    agg: avg
    target: = 95%
    interpretation: Low compliance increases failure risk
    lineage: fact_maintenance[PM On Time], fact_maintenance[PM Planned]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag assets with MTBF below target and MTTR above target.
- Escalate unplanned downtime % above threshold for 2 consecutive periods.
- Flag PM compliance below target and correlate with downtime trend.
- Flag spare-part stockouts above threshold for critical assets.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:

  - kpi: ops.mtbf.hours
    condition: <
    threshold: asset_target
    scope: asset_month
    exclusion: ramp-up assets
    action_code: O2

  - kpi: ops.mttr.hours
    condition: >
    threshold: asset_target
    scope: asset_month
    exclusion: major_overhauls
    action_code: L2

  - kpi: ops.downtime.unplanned.pct
    condition: >
    threshold: 0.05
    scope: last_2_periods
    exclusion: planned_shutdowns
    action_code: O2

  - kpi: ops.pm_compliance.pct
    condition: <
    threshold: 0.95
    scope: month
    exclusion: deferred_by_design
    action_code: O2

  - kpi: ops.spare_parts.stockout.pct
    condition: >
    threshold: 0.02
    scope: critical_assets
    exclusion: none
    action_code: D1
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| O2 | Operations Stabilisation | Unplanned downtime %, MTBF/MTTR off target | Address root causes, improve maintenance scheduling | Improve availability, reduce unplanned downtime | L2 | Ops Excellence / Maintenance |
| L2 | Quality & Yield (repurposed for maintainability) | MTTR above target | Standardize repair procedures, tooling | Reduce MTTR, improve availability | L2 | Maintenance |
| D1 | Cost Take-Out / Parts Readiness | Spare-part stockouts > threshold | Improve spare-part planning, vendor SLAs | Reduce stockouts, improve MTTR/availability | L2 | Maintenance / Procurement |
| M2 | Performance Uplift | Performance losses linked to maintenance issues | Optimize setups, reduce micro-stops | Improve performance %, throughput | L2 | Production / Maintenance |

---

## 6. 3-30-300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Availability %  
- MTBF (hours)  
- MTTR (hours)  
- Unplanned Downtime %  
- PM Compliance %  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Availability vs Target by Asset | Column | dim_asset[Asset] | [Availability %], [Target] | Plant | Current month | Core ranking |
| MTBF / MTTR Trend | Line | dim_date[Month] | [MTBF], [MTTR] | Asset Class | L12M | Reliability view |
| Unplanned Downtime by Cause | Bar (horizontal) | fact_ops_failures[Cause] | [Unplanned Downtime Minutes] | Asset | Last 3 months | Pareto |
| PM Compliance vs Downtime | Scatter | [PM Compliance %] | [Unplanned Downtime %] | Asset | Current quarter | Correlation |

### 6.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Plant / Asset / Asset Class  
- Criticality / Maintenance Type  

---

### 6.4 300-Second Layer (Diagnostics)

- (optional)

## 7. Data Requirements Summary

```yaml
required_facts:

  - fact_ops (availability/downtime)

  - fact_ops_failures (MTBF/MTTR with causes)

  - fact_maintenance (PM compliance, orders)
required_dimensions:

  - dim_date

  - dim_org (plant/line/asset)

  - dim_asset (if separate from org)

  - security_user_org
required_grain: asset_day for availability; failure event for MTBF/MTTR; month for PM compliance
required_time_range: 12-24 months history
required_slicers: Date, Plant/Asset, Asset Class/Criticality
```

---

## 8. Dependencies, Assumptions & Constraints

- Failure events accurately timestamped; planned vs unplanned downtime coded.
- PM schedule exists; compliance measured; asset hierarchy stable.
- Spare-part stockouts recorded; critical assets flagged.
- OneLake canonical dims used (dim_date, dim_org/security_user_org; dim_asset if separate).

---

## 9. Success Criteria

- Impact: Reduce unplanned downtime % below target; MTBF improves to targets; MTTR reduced; PM compliance = target; stockouts reduced.  
- Adoption: Used in weekly maintenance/reliability reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly maintenance and monthly reliability review.

---

## 10. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime skews availability.  
- MTBF/MTTR distorted by missing or merged failure events.  
- PM compliance percentages misleading if plan not realistic or if deferrals aren't flagged.  


