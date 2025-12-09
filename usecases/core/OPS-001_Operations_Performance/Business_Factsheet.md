# OPS-001 – Operations Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** OPS-001
- **Domain:** Operations
- **Owner (Business):** COO / Plant Manager / Ops Excellence
- **Reporting Level:** Tactical / Operational
- **Analytics Stage:** Diagnostic
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Improve operational efficiency across plants and lines by monitoring OEE and its drivers.  
**Business Value:** +2–4 pp OEE, fewer bottlenecks, lower unit cost.  
**Out of Scope:** Deep maintenance strategy (covered in OPS-002), cost optimization (FIN-002).

---

## 2. Core Questions
- Where is OEE below target by plant/line/shift?
- Is the gap driven by Availability, Performance, or Quality?
- Which downtime reasons drive the largest losses?
- How do shifts or product mixes influence throughput?
- Which lines deliver best-practice performance that can be replicated?

**Example Queries:**
- “Which top 5 lines have the largest OEE gap vs target this month?”
- “What is the downtime reason Pareto for Line A in the last 30 days?”

---

## 3. KPI Set (Business View)

| KPI Name            | KPI ID (mandatory)   | Purpose                  | Definition (short)                                   | Unit / Format | Target / Threshold          | Interpretation                         |
|---------------------|----------------------|--------------------------|------------------------------------------------------|---------------|-----------------------------|----------------------------------------|
| OEE %               | ops.oee.pct          | Overall efficiency       | Availability % × Performance % × Quality %           | %             | ≥ 80–85 % core lines        | Overall line effectiveness             |
| Availability %      | ops.availability.pct | Runtime discipline       | Run Time / Planned Time                              | %             | ≥ 90 %                      | Schedule adherence vs downtime         |
| Performance %       | ops.performance.pct  | Speed efficiency         | Actual Output / (Run Time × Ideal Rate)              | %             | ≥ 95 %                      | Speed losses vs ideal                  |
| Quality %           | ops.quality.pct      | First-pass quality       | Good Units / (Good + Scrap Units)                    | %             | ≥ 98 %                      | Scrap/rework pressure                  |
| Throughput Units    | ops.throughput.units | Volume output            | Good Units produced                                  | units         | Trend vs plan               | Output volume                          |
| Downtime Minutes %  | ops.downtime.pct     | Loss visibility          | Downtime Minutes / Planned Time                      | %             | ≤ 5 %                       | Unplanned downtime control             |

> Use KPI IDs from the catalog; set explicit targets or bands per site/line.

---

## 4. Business Logic & Thresholds
- OEE % < target for 2 consecutive weeks → issue.
- Availability % < 90 % OR Performance % < 95 % OR Quality % < 98 % → classify driver and owner.
- Downtime Minutes % > 5 % with repeating category → escalate to maintenance.
- Throughput Units below plan >3 % with stable OEE → check mix/plan assumptions.

**Trigger Logic (formal, for automation):**
```
WHEN ops.oee.pct < target_plant_line
OR   ops.availability.pct < 90
OR   ops.performance.pct < 95
OR   ops.quality.pct < 98
THEN propose M2 (quick fixes), O2 (maintenance action), PC4 (process stabilisation)
```

---

## 5. Action Codes

| Code | Name                       | Trigger (formal, KPIs)                                  | Description (business action)                     | Expected KPI Impact        |
|------|----------------------------|---------------------------------------------------------|---------------------------------------------------|----------------------------|
| M2   | Maintenance Quick Fix      | downtime.pct > 5 % and repeating reason                 | Fast-track fix for top downtime reasons           | +1–2 pp Availability %     |
| O2   | Planned Maintenance Window | availability.pct < 90 % for 2 weeks                     | Schedule planned maintenance and calibrations     | +1–3 pp Availability %     |
| PC4  | Process Stabilisation      | performance.pct < 95 % or quality.pct < 98 %            | Adjust speed, SOPs, training to stabilize process | +1–2 pp Performance/Quality|
| L2   | Line Balancing             | throughput.units below plan with bottleneck identified  | Rebalance tasks/crew to remove bottlenecks        | +1–3 % Throughput Units    |

> Reference ActionCodes_Portfolio; keep triggers KPI-based.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- OEE %, Availability %, Performance %, Quality %, Downtime Minutes %.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name            | Type    | X-Axis / Category    | Y-Axis / Value                              | Segment / Legend | Filters / Defaults     |
|------------------------|---------|----------------------|---------------------------------------------|------------------|------------------------|
| OEE Trend vs Target    | Line    | dim_date[Month]      | [OEE %], Target                             | Plant/Line       | Last 12–18 months      |
| OEE by Plant/Line      | Column  | dim_org[Plant/Line]  | [OEE %], [Availability %], [Performance %]  | Region/Country   | Top/Bottom N           |
| Downtime Pareto        | Bar     | dim_downtime_reason[DowntimeReason] | [Downtime Minutes]              | DowntimeCategory  | Current period         |
| Shift Performance      | Column  | dim_date[Shift]      | [OEE %], [Availability %], [Performance %]   | Plant/Line       | Last 30 days           |
| Detail Matrix          | Matrix  | Region > Plant > Line > Shift | OEE %, Availability %, Performance %, Quality %, Throughput Units | Region | Export enabled |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Drill: Region → Plant → Line → Shift → Downtime Reason.
- Export: downtime table with reason, duration, responsible owner, and action code.

---

## 7. Dependencies, Assumptions & Constraints
- Data: planned time, runtime, downtime reason/category, ideal rate, good/scrap units; stable org hierarchy; shift calendar.
- Assumptions: Targets per plant/line maintained; downtime reasons standardized.
- Constraints: Missing reason codes reduce insight; unreliable ideal rates skew Performance %.

---

## 8. Success Criteria
- Leading: >80 % usage in daily/weekly ops reviews; action log maintained with owners.
- Lagging: OEE % improves toward target; downtime % decreases; throughput plan adherence improves.
- Cadence/Quality: Weekly review; no KPI-definition conflicts across plants.
