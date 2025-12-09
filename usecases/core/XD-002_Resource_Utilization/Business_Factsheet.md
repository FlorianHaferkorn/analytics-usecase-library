# XD-002 – Resource Utilization (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** XD-002
- **Domain:** Customer Experience / Operations
- **Owner (Business):** Head of Customer Service / Workforce Management
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/experience.yaml
- **Related Semantic Model:** semantic_models/domains/experience/model_definition.yaml

---

## 1. Summary
**Purpose:** Optimize workforce utilization and staffing to hit service targets at minimal cost.  
**Business Value:** Lower overtime and idle cost, higher SLA attainment, better agent productivity and quality.  
**Out of Scope:** Long-term hiring strategy; labor relations topics.

---

## 2. Core Questions
- Are we over- or under-staffed by channel/queue/interval?
- Where do occupancy and utilization drift from targets?
- How do staffing gaps impact SLA, backlog, and quality (AHT/FCR)?
- Which shifts/skills need rebalancing or cross-training?

**Example Queries:**
- “Which queues had occupancy >90% and still missed SLA last week?”
- “Where can we reassign capacity to reduce backlog fastest?”

---

## 3. KPI Set (Business View)

| KPI Name           | KPI ID (mandatory)          | Purpose                        | Definition (short)                                | Unit / Format | Target / Threshold       | Interpretation                  |
|--------------------|-----------------------------|--------------------------------|---------------------------------------------------|---------------|--------------------------|---------------------------------|
| Utilization %      | res.utilization.pct         | Productivity                   | Work time / Paid time                             | %             | 75–85% (by channel)      | Capacity use                    |
| Occupancy %        | res.occupancy.pct           | Load vs availability           | Handle + Wrap / Logged-in                         | %             | 80–90%                   | Real-time load                  |
| SLA Attainment %   | svc.sla.attainment.pct      | Service reliability            | % interactions meeting SLA                        | %             | ≥ 95%                    | Outcome                         |
| Overtime %         | res.overtime.pct            | Cost and sustainability        | Overtime hours / total hours                      | %             | ≤ 5%                     | Cost/strain indicator           |
| Shrinkage %        | res.shrinkage.pct           | Plan realism                   | Non-productive time / paid time                   | %             | ≤ plan                   | Planning quality                |
| Backlog Volume     | svc.backlog.count           | Work pressure                 | Open cases/tickets                                | count         | Trend ↓                  | Service risk                    |

> Align KPI IDs to catalog; targets vary by channel/skill.

---

## 4. Business Logic & Thresholds
- Utilization < 70% with SLA met → overstaffing; reassign or reduce planned hours.
- Occupancy > 90% with SLA misses → add capacity or deflect demand.
- Overtime % > 5% for 2 periods → schedule fix/cross-training.
- Shrinkage above plan → investigate absenteeism/planning accuracy.

**Trigger Logic (formal, for automation):**
```
WHEN res.utilization.pct < 70 AND svc.sla.attainment.pct >= 95
OR   res.occupancy.pct > 90 AND svc.sla.attainment.pct < 95
OR   res.overtime.pct > 5
OR   res.shrinkage.pct > plan_shrinkage
THEN propose L2 (staffing/routing), D1 (demand deflection), O2 (process efficiency), PC4 (schedule optimization)
```

---

## 5. Action Codes

| Code | Name                           | Trigger (formal, KPIs)                         | Description (business action)                     | Expected KPI Impact                |
|------|--------------------------------|------------------------------------------------|---------------------------------------------------|------------------------------------|
| L2   | Staffing / Routing Optimise    | occupancy.pct > 90 OR utilization.pct < 70     | Rebalance shifts/queues; dynamic routing          | Higher SLA, balanced utilization   |
| PC4  | Schedule Optimisation          | overtime.pct > 5 OR shrinkage > plan           | Fix schedules, breaks, adherence                   | Lower overtime, better occupancy   |
| O2   | Process Efficiency             | aht above target impacting occupancy           | SOP/automation to reduce AHT                       | Lower AHT, improved utilization    |
| D1   | Demand Management              | volume surge drives SLA/occupancy issues       | Deflect/shift demand to digital/self-service       | Lower load, better SLA             |

> Use ActionCodes_Portfolio; ensure KPI-based triggers.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- Utilization %, Occupancy %, SLA %, Overtime %, Shrinkage %, Backlog.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name               | Type   | X-Axis / Category          | Y-Axis / Value                            | Segment / Legend | Filters / Defaults |
|---------------------------|--------|----------------------------|-------------------------------------------|------------------|--------------------|
| Utilization vs Target     | Column | dim_queue[Queue]           | [Utilization %], Target                   | Channel/Region   | Current period     |
| Occupancy Trend           | Line   | dim_date[Week/Day]         | [Occupancy %], [SLA %]                    | Channel/Queue    | Last 4–8 weeks     |
| Overtime & Shrinkage      | Column | dim_date[Week]             | [Overtime %], [Shrinkage %]               | Region           | Last 8 weeks       |
| Backlog by Queue          | Column | dim_queue[Queue]           | [Backlog Count]                           | Priority         | Current period     |
| Capacity vs Demand        | Line   | dim_date[Interval/Hour]    | Planned FTE vs Actual Volume/Workload     | Channel          | Last 7–30 days     |
| Detail Matrix             | Matrix | Region > Channel > Queue   | Utilization %, Occupancy %, SLA %, Overtime %, Shrinkage %, Backlog | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Channel → Queue → Interval → Agent; show adherence, absenteeism, AHT, SLA.
- Export: staffing plan vs actual, overtime drivers, backlog age by priority.

---

## 7. Dependencies, Assumptions & Constraints
- Data: WFM schedules, logged-in time, handle/wrap time, paid hours, overtime, shrinkage codes, volume by interval, SLA outcomes, backlog by queue/priority.
- Assumptions: Targets by queue/channel; adherence captured; shrinkage categories defined.
- Constraints: Missing adherence/shrinkage reduces accuracy; inconsistent timezones skew occupancy.

---

## 8. Success Criteria
- Leading: >80% usage in weekly WFM/ops reviews; schedule adherence tracked; action log maintained.
- Lagging: SLA at/above target with lower overtime; utilization/occupancy within bands; backlog stable/down.
- Cadence/Quality: Weekly ops review; daily monitoring; KPI definitions consistent across regions/channels.
