# XD-002 — Resource Utilization  

## Business Factsheet (v1.2)

---

## 0. Metadata (Mandatory)

- **Use Case ID:** XD-002
- **Domain:** Experience / Service
- **Business Owner:** Head of Customer Service / Workforce Management
- **KPI Owner:** Service Operations / Workforce Planning
- **Decision Owner:** CX/Service Leadership
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/experience.yaml
- **Related Semantic Model:** semantic_models/domains/experience/model_definition.yaml

---

## 1. Business Summary

**Purpose:** Optimize resource utilization and occupancy while protecting SLA and customer experience.  
**Business Value:** Better staffing efficiency, reduced overtime/shrinkage costs, and controlled backlog without SLA degradation.  
**Out of Scope:** Detailed SLA performance drivers (XD-001); sales pipeline; field service dispatching.

---

## 2. Core Business Questions

- What are utilization and occupancy by channel/queue/region vs targets?
- How do overtime and shrinkage affect SLA attainment and backlog?
- Where do staffing imbalances create SLA risk or idle capacity?
- Which actions improve utilization without harming quality?

**Example Query Patterns (optional):**

- “Which queues have utilization below target and SLA/backlog risk?”
- “Where is overtime rising while shrinkage is high?”

---

## 3. Required KPIs (Mandatory)

All KPIs must exist in the KPI Catalog.

```yaml
required_kpis:
  - id: res.utilization.pct
    name: Utilization %
    purpose: Productive time vs paid time
    definition_short: (Talk/Work Time) / Paid Time
    unit: %
    grain: agent_day or queue_day
    agg: avg
    target: ≥ target band
    interpretation: Low utilization shows underuse; too high risks quality
    lineage: fact_wfm[Work Time], fact_wfm[Paid Time]
  - id: res.occupancy.pct
    name: Occupancy %
    purpose: Active time vs available time
    definition_short: (Talk + Wrap) / (Talk + Wrap + Idle)
    unit: %
    grain: agent_day or queue_day
    agg: avg
    target: Target band
    interpretation: Too high occupancy risks burnout/AHT; too low wastes capacity
    lineage: fact_wfm[Talk], fact_wfm[Wrap], fact_wfm[Idle]
  - id: svc.sla.attainment.pct
    name: SLA Attainment %
    purpose: Service level compliance
    definition_short: Cases meeting SLA / total cases
    unit: %
    grain: day_queue
    agg: avg
    target: ≥ target
    interpretation: Low attainment signals service failure
    lineage: fact_cases[SLA Met Flag]
  - id: res.overtime.pct
    name: Overtime %
    purpose: Cost and fatigue
    definition_short: Overtime hours / Total hours
    unit: %
    grain: agent_day or region_week
    agg: avg
    target: ≤ target
    interpretation: High overtime signals staffing gaps
    lineage: fact_wfm[Overtime Hours], fact_wfm[Total Hours]
  - id: res.shrinkage.pct
    name: Shrinkage %
    purpose: Non-productive time
    definition_short: Non-productive time / Paid time
    unit: %
    grain: agent_day
    agg: avg
    target: Within target band
    interpretation: High shrinkage reduces available capacity
    lineage: fact_wfm[Shrinkage], fact_wfm[Paid Time]
  - id: svc.backlog.count
    name: Backlog Count
    purpose: Workload risk
    definition_short: Open cases not resolved
    unit: count
    grain: day_queue
    agg: sum
    target: Reduce vs target
    interpretation: Rising backlog risks SLA failure
    lineage: fact_cases[Backlog Flag/Open Cases]
```

---

## 4. Business Logic & Thresholds

Formal rules that define performance and action triggers.

### 4.1 Logic Description

- Flag utilization/occupancy outside target bands (too low or too high).
- Flag rising overtime and shrinkage; correlate with SLA and backlog.
- Identify queues/regions with backlog risk due to capacity gaps.

### 4.2 Formal Trigger Rules (Machine-Readable)

```yaml
triggers:
  - kpi: res.utilization.pct
    condition: outside
    threshold: [util_lower, util_upper]
    scope: queue_region_channel
    exclusion: training/new hires
    action_code: O2
  - kpi: res.occupancy.pct
    condition: outside
    threshold: [occ_lower, occ_upper]
    scope: queue_region_channel
    exclusion: training/new hires
    action_code: O2
  - kpi: res.overtime.pct
    condition: >
    threshold: overtime_target
    scope: queue_region
    exclusion: crisis
    action_code: M2
  - kpi: res.shrinkage.pct
    condition: >
    threshold: shrinkage_target
    scope: queue_region
    exclusion: planned_absences
    action_code: O2
```

---

## 5. Action Codes (Mandatory)

Link business behavior to measurable outcomes.

| Action Code | Name | Trigger (formal) | Description | Expected KPI Impact | Level (L1/L2/L3) | Owner |
|-------------|------|------------------|-------------|---------------------|------------------|-------|
| O2 | Operations Stabilisation | Utilization/Occupancy outside band; backlog risk | Rebalance staffing, reforecast WFM, adjust routing | Improve SLA, balance utilization | L2 | Service Ops / WFM |
| M2 | Performance Uplift | Overtime high | Shift mix, cross-train, automation to reduce overtime | Reduce overtime, stabilize SLA | L2 | WFM / Service Ops |
| L2 | Quality & Yield | High shrinkage or low FCR tied to resource issues | Training/coaching, process fixes | Reduce shrinkage, improve FCR/SLA | L2 | CX/Training |
| D1 | Cost Take-Out | Excess capacity/inefficient shift mix | Optimize staffing, reduce idle time | Reduce cost-to-serve | L2 | Service Ops / Finance |

---

## 6. 3–30–300 Page Layout (Mandatory)

### 6.1 3-Second Layer (KPI Cards)

- Utilization %  
- Occupancy %  
- Overtime %  
- Shrinkage %  
- SLA % / Backlog Count  

### 6.2 30-Second Layer (Main Visuals)

| Visual Name | Visual Type | X-Axis | Y-Axis | Segment | Default Filter | Notes |
|-------------|-------------|--------|--------|---------|----------------|-------|
| Utilization vs Band by Queue | Column | dim_org[Queue] | [Utilization %], Band | Channel/Region | Current month | Core ranking |
| Occupancy vs Band | Column | dim_org[Queue] | [Occupancy %], Band | Channel/Region | Current month | Balance view |
| Overtime & Shrinkage Trend | Line | dim_date[Week] | [Overtime %], [Shrinkage %] | Region/Channel | L12W | Capacity health |
| SLA vs Backlog | Scatter | [SLA %] | [Backlog Count] | Queue/Region | Current quarter | Service risk |

### 6.3 Required Slicers (Mandatory)

- Date (Week/Month)  
- Region / Channel / Queue  
- Agent Group / Skill (if available)  

---

## 7. Data Requirements Summary

```yaml
required_facts:
  - fact_wfm (work/idle/wrap/overtime/shrinkage)
  - fact_cases (SLA, backlog)
required_dimensions:
  - dim_date
  - dim_org (region/channel/queue)
  - dim_queue (if separate)
  - security_user_org
required_grain: agent_day or queue_day; week/month for trends
required_time_range: 12–24 months history
required_slicers: Date, Region/Channel/Queue, Agent Group/Skill (if available)
```

---

## 8. Dependencies, Assumptions & Constraints

- WFM data includes work/idle/wrap, overtime, shrinkage; SLA/backlog available from cases.
- Target bands defined for utilization/occupancy; exclusions for training/ramp-up.
- OneLake canonical dims used (dim_date, dim_org, security_user_org).
- Data latency ≤24h.

---

## 9. Success Criteria

- Impact: Utilization/occupancy within bands; overtime/shrinkage reduced; SLA stable/improved; backlog controlled.  
- Adoption: Used in weekly WFM/service ops reviews; action codes triggered with <5% false positives.  
- Quality: KPI definitions consistent across XD-001/002; reconciled to source totals.  
- Decision Frequency: Weekly and daily staffing reviews.

---

## 10. Risks & Wrong Interpretations (Short)

- Overdriving utilization causing quality decline.  
- Misclassifying shrinkage leading to wrong capacity view.  
- Ignoring seasonality causing false alarms on utilization/occupancy.  
