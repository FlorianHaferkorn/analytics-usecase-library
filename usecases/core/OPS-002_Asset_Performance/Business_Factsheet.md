---
id: OPS-002
factsheet_type: business
---

# OPS-002 - Asset Performance  

## Business Factsheet

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

  - id: ops.failure.count
    name: Failure Count
    purpose: Failure volume
    definition_short: Count of failure events
    unit: count
    grain: asset_month
    agg: sum
    target: Reduce vs baseline
    interpretation: Higher counts indicate lower reliability
    lineage: fact_ops[Failure Count]

  - id: ops.inventory.value.amount
    name: Inventory Value Amount
    purpose: Spare parts guardrail
    definition_short: Inventory value for spare parts
    unit: EUR
    grain: sku_month
    agg: sum
    target: Maintain within budget
    interpretation: Higher values indicate more capital tied in spares
    lineage: fact_inventory[Inventory Value Amount]

  - id: ops.pm.task.count
    name: Preventive Maintenance Task Count
    purpose: PM workload
    definition_short: Count of PM tasks
    unit: count
    grain: asset_month
    agg: sum
    target: Meet plan
    interpretation: Tracks PM execution volume
    lineage: fact_maintenance[PM Task Count]

  - id: ops.safety.incident.count
    name: Safety Incident Count
    purpose: Safety guardrail
    definition_short: Count of safety incidents
    unit: count
    grain: site_month
    agg: sum
    target: = 0
    interpretation: Higher counts indicate elevated safety risk
    lineage: fact_safety[Incident Count]
```

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).

```yaml
action_codes:

  - id: O-A2.1
    name: Reliability Orchestration
    purpose: Coordinate Asset Reliability Interventions
    status: active
    owner: Maintenance Manager
    trigger_kpis: [ops.availability.pct, ops.downtime.unplanned.pct]
    guardrail_kpis: [ops.pm_compliance.pct]
    outcome_kpis: [ops.availability.pct]
    impact_range: ops.availability.pct: 2.0-6.0 pp
    levels: L1-L3
    definition: framework\action_codes\Operations\O-A2.1.yaml

  - id: O-A2.2
    name: Failure Reduction (MTBF Improvement)
    purpose: Reduce Failure Frequency and Improve MTBF
    status: active
    owner: Reliability Engineer
    trigger_kpis: [ops.mtbf.hours]
    guardrail_kpis: [ops.pm_compliance.pct]
    outcome_kpis: [ops.mtbf.hours, ops.availability.pct]
    impact_range: ops.mtbf.hours: 10.0-30.0 %
    levels: L1-L3
    definition: framework\action_codes\Operations\O-A2.2.yaml

  - id: O-A2.3
    name: Repair Time Reduction (MTTR Control)
    purpose: Reduce Mean Time to Repair for Faster Recovery
    status: active
    owner: Maintenance Supervisor
    trigger_kpis: [ops.mttr.hours]
    guardrail_kpis: [ops.safety.incident.count]
    outcome_kpis: [ops.mttr.hours, ops.availability.pct]
    impact_range: ops.mttr.hours: -10.0--30.0 %
    levels: L1-L3
    definition: framework\action_codes\Operations\O-A2.3.yaml

  - id: O-A2.4
    name: Preventive Maintenance Discipline
    purpose: Enforce PM Compliance to Prevent Failures
    status: active
    owner: Maintenance Planner
    trigger_kpis: [ops.pm_compliance.pct]
    guardrail_kpis: [ops.availability.pct]
    outcome_kpis: [ops.pm_compliance.pct, ops.mtbf.hours]
    impact_range: ops.pm_compliance.pct: 5.0-10.0 pp
    levels: L1-L3
    definition: framework\action_codes\Operations\O-A2.4.yaml

  - id: O-A2.5
    name: Spare Parts Readiness
    purpose: Eliminate Repair Delays from Missing Spare Parts
    status: active
    owner: Maintenance Supply Coordinator
    trigger_kpis: [ops.spare_parts.stockout.pct]
    guardrail_kpis: [ops.inventory.value.amount]
    outcome_kpis: [ops.spare_parts.stockout.pct, ops.mttr.hours]
    impact_range: ops.spare_parts.stockout.pct: -5.0--15.0 pp
    levels: L1-L3
    definition: framework\action_codes\Operations\O-A2.5.yaml
```

---

## 5. 3-30-300 Page Layout (Mandatory)

### 5.1 3-Second Layer (KPI Cards)

- Availability %  
- MTBF (hours)  
- MTTR (hours)  
- Unplanned Downtime %  
- PM Compliance %  

### 5.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Availability vs Target by Asset | Column | dim_asset[Asset] | [Availability %], [Target] | Plant | Current month | Core ranking |
| MTBF / MTTR Trend | Line | dim_date[Month] | [MTBF], [MTTR] | Asset Class | L12M | Reliability view |
| Unplanned Downtime by Cause | Bar (horizontal) | fact_ops_failures[Cause] | [Unplanned Downtime Minutes] | Asset | Last 3 months | Pareto |
| PM Compliance vs Downtime | Scatter | [PM Compliance %] | [Unplanned Downtime %] | Asset | Current quarter | Correlation |

### 5.3 Required Slicers (Mandatory)

- Date (Month/Quarter)  
- Plant / Asset / Asset Class  
- Criticality / Maintenance Type  

---

### 5.4 300-Second Layer (Diagnostics)

- (optional)

## 6. Data Requirements Summary

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

## 7. Dependencies, Assumptions & Constraints

- Failure events accurately timestamped; planned vs unplanned downtime coded.
- PM schedule exists; compliance measured; asset hierarchy stable.
- Spare-part stockouts recorded; critical assets flagged.
- OneLake canonical dims used (dim_date, dim_org/security_user_org; dim_asset if separate).

---

## 8. Success Criteria

- Impact: Reduce unplanned downtime % below target; MTBF improves to targets; MTTR reduced; PM compliance = target; stockouts reduced.  
- Adoption: Used in weekly maintenance/reliability reviews; action codes triggered with <5% false positives.  
- Quality: Cause coding coverage high; KPI definitions consistent across ops UCs.  
- Decision Frequency: Weekly maintenance and monthly reliability review.

---

## 9. Risks & Wrong Interpretations (Short)

- Misclassified planned vs unplanned downtime skews availability.  
- MTBF/MTTR distorted by missing or merged failure events.  
- PM compliance percentages misleading if plan not realistic or if deferrals aren't flagged.  



