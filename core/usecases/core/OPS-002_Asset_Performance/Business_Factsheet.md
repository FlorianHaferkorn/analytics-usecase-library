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
- **Related Data Contract:** core/data_contracts/domains/operations.yaml
- **Related Semantic Model:** Framework: core/strategy_operating_model/operating_model/semantic_layer.md. Aurora: showcases/aurora_group/semantic_models/Operations.SemanticModel (domain model for OPS-*).

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

### 3. KPI & Action Code Overview

| KPI ID | Role |
|--------|------|
| ops.mtbf.hours | Strategic |
| ops.availability.pct | Influencing |
| ops.mttr.hours | Influencing |
| ops.downtime.unplanned.pct | Influencing |
| ops.spare_parts.stockout.pct | Influencing |
| ops.pm_compliance.pct | Influencing |
| ops.failure.count | Influencing |
| ops.inventory.value.amount | Influencing |
| ops.pm.task.count | Influencing |
| ops.safety.incident.count | Influencing |

**Action Codes:** O-A2.1, O-A2.2, O-A2.3, O-A2.4, O-A2.5

> Full machine-readable configuration in `UseCase_Bracket.yaml` (SSOT).

---

## 4. Action Codes (Summary)

Structured summary of action codes (definitions remain in YAML).


> Machine-readable KPI + Action configuration has been extracted to `UseCase_Bracket.yaml` (SSOT).
> This factsheet focuses on business context only.


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






## 10. Typical Decision Scenarios

These scenarios illustrate how this use case drives decisions in practice. They are examples — not exhaustive.

### Scenario A: MTBF Collapse on Critical Production Line

**Situation:** Mean time between failures on Line 3 dropped from 480h to 190h over 8 weeks. Unplanned downtime increased to 12%. Spare parts stockout rate is 18% for Line 3 components.

**Decision question:** Is this a maintenance execution gap (missed PMs), an aging asset issue, or a spare parts availability problem?

**Who decides:** Maintenance Manager + Plant Director.

**Consequence of inaction:** Each unplanned stop costs ~€15K in lost output; current trajectory projects 3 additional failures per month.

**Action Code triggered:** O-A2.1 (Asset Reliability Recovery) — activates failure pattern analysis and PM compliance review.

### Scenario B: High PM Compliance but No MTBF Improvement

**Situation:** Preventive maintenance compliance is 95%, yet MTBF has not improved in 6 months. Failure modes are shifting from mechanical to electrical/control system issues.

**Decision question:** Is the PM program targeting the right failure modes, or does the maintenance strategy need updating?

**Who decides:** Reliability Engineer + Maintenance Manager.

**Consequence of inaction:** PM resources are spent without reliability gain; false sense of proactive maintenance.

**Action Code triggered:** O-A2.3 (Maintenance Strategy Review) — activates failure mode analysis and PM task relevance scoring.
