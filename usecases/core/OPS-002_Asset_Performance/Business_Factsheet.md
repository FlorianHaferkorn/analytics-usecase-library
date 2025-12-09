# OPS-002 – Asset Performance (Business Factsheet)

## 0. Metadata (Mandatory)
- **Use Case ID:** OPS-002
- **Domain:** Operations
- **Owner (Business):** COO / Head of Maintenance / Reliability Engineering
- **Reporting Level:** Tactical
- **Analytics Stage:** Diagnostic / Prescriptive
- **Related Data Contract:** data_contracts/domains/operations.yaml
- **Related Semantic Model:** semantic_models/domains/scm/model_definition.yaml

---

## 1. Summary
**Purpose:** Increase asset uptime and reliability while controlling maintenance and spare-parts cost.  
**Business Value:** Higher availability, fewer breakdowns, lower MTTR/maintenance spend, better service adherence.  
**Out of Scope:** Long-term capex portfolio decisions (handled in finance/capex processes).

---

## 2. Core Questions
- Which assets show the highest downtime and failure frequency?
- What are the root causes and patterns behind unplanned downtime?
- How effective are preventive plans vs corrective work?
- Where do spare parts stockouts create MTTR spikes?
- Which assets need overhaul, redesign, or replacement?

**Example Queries:**
- “Which top 10 assets by criticality drove 80% of downtime last month?”
- “How does MTBF trend by asset class vs PM compliance?”

---

## 3. KPI Set (Business View)

| KPI Name              | KPI ID (mandatory)           | Purpose                        | Definition (short)                   | Unit / Format | Target / Threshold            | Interpretation                    |
|-----------------------|------------------------------|--------------------------------|--------------------------------------|---------------|-------------------------------|-----------------------------------|
| Availability %        | ops.availability.pct         | Uptime performance             | Run Time / Planned Time              | %             | ≥ 95 % (critical assets)      | Overall uptime                    |
| MTBF (hours)          | ops.mtbf.hours               | Reliability                    | Mean time between failures           | hours         | ↑ vs prior period             | Reliability trend                 |
| MTTR (hours)          | ops.mttr.hours               | Repair efficiency              | Mean time to repair                  | hours         | ↓ vs prior period             | Recovery speed                    |
| Unplanned Downtime %  | ops.downtime.unplanned.pct   | Stability                      | Unplanned Downtime / Total Downtime  | %             | ≤ 30–40 %                     | Control of unexpected events      |
| Spare Parts Stockout %| ops.spare_parts.stockout.pct | Readiness                      | Stockout events / Parts requests     | %             | ≤ 2–3 % for critical parts    | Parts readiness risk              |
| PM Compliance %       | ops.pm_compliance.pct        | Preventive discipline          | Completed PM / Planned PM            | %             | ≥ 90 %                        | Preventive execution              |

> Keep KPI IDs aligned to the catalog; set thresholds per asset criticality.

---

## 4. Business Logic & Thresholds
- Availability % < 95 % for critical assets → reliability program.
- MTBF decreasing AND MTTR increasing → asset health degradation, escalate.
- Unplanned Downtime % > 40 % → redesign maintenance schedule/root cause program.
- Spare Parts Stockout % > 3 % on critical parts → adjust safety stock and supplier SLAs.
- PM Compliance % < 90 % → enforce scheduling and crew productivity.

**Trigger Logic (formal, for automation):**
```
WHEN ops.availability.pct < target_asset
OR   ops.downtime.unplanned.pct > 40
OR   ops.mtbf.hours declines 3 periods in a row
OR   ops.spare_parts.stockout.pct > 3
THEN propose M2 (maintenance optimisation), O2 (root-cause program), PC4 (spare-parts policy)
```

---

## 5. Action Codes

| Code | Name                            | Trigger (formal, KPIs)                         | Description (business action)                       | Expected KPI Impact        |
|------|---------------------------------|------------------------------------------------|-----------------------------------------------------|----------------------------|
| M2   | Maintenance Optimisation        | availability.pct < target AND unplanned.pct > 40| Rebalance PM/CM mix, schedule by criticality        | +1–3 pp Availability %     |
| O2   | Root Cause Elimination          | recurring failures, falling MTBF               | RCA, redesign, Poka-Yoke                            | Higher MTBF, lower MTTR    |
| PC4  | Spare-Parts Policy Tuning       | stockout.pct > 3 % critical parts              | Adjust safety stock, supplier SLAs, reorder points  | Lower MTTR, fewer stockouts|
| L2   | Field Crew Productivity         | rising MTTR without new failures               | Improve dispatching, skills, and SOPs               | Lower MTTR                 |

> Use ActionCodes_Portfolio as single source; keep triggers KPI-based.

---

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer (KPI Cards)
- Availability %, MTBF, MTTR, Unplanned Downtime %, Spare Parts Stockout %, PM Compliance %.

### 6.2 30-Second Layer (Main Visuals)
| Visual Name               | Type   | X-Axis / Category           | Y-Axis / Value                                  | Segment / Legend | Filters / Defaults  |
|---------------------------|--------|-----------------------------|-------------------------------------------------|------------------|---------------------|
| Availability Trend        | Line   | dim_date[Month]             | [Availability %], Target                        | Plant/AssetClass | Last 12–24 months   |
| Reliability Trend         | Line   | dim_date[Month]             | [MTBF (hours)], [MTTR (hours)]                  | AssetClass       | Last 12–24 months   |
| Downtime Pareto           | Bar    | dim_failure[FailureReason]  | [Downtime Minutes]                              | FailureCategory  | Current period      |
| Asset Uptime Ranking      | Column | dim_asset[AssetName]        | [Availability %], [Unplanned Downtime %]        | Plant            | Top/Bottom N        |
| PM Compliance by Plant    | Column | dim_org[Plant]              | [PM Compliance %]                               | Region           | Last full month     |
| Spare Parts Stockouts     | Column | dim_part[PartCategory]      | [Spare Parts Stockout %]                        | Criticality      | Last 90 days        |

### 6.3 300-Second Layer (Diagnostics & Detail)
- Matrix: Region > Plant > AssetClass > Asset with Availability %, MTBF, MTTR, Unplanned Downtime %, PM Compliance %, Stockout %; export enabled.
- Drill: Asset → Work Orders → Failure Reason → Part usage; pre-filter by criticality.

---

## 7. Dependencies, Assumptions & Constraints
- Data: CMMS/EAM work orders with failure reason, timestamps, downtime, repair time; asset hierarchy and criticality; PM schedule and completion; spare parts stock levels and requests.
- Assumptions: Targets per asset class maintained; PM completion timestamps captured; failure coding standardised.
- Constraints: Missing failure codes limit root-cause analytics; poor part-master mapping hides stockout root causes.

---

## 8. Success Criteria
- Leading: >80 % usage in weekly maintenance reviews; action log maintained with owner and due date.
- Lagging: Availability % moves toward target; MTBF rising, MTTR falling; unplanned downtime share dropping; stockouts declining for critical parts.
- Cadence/Quality: Weekly review; consistent KPI definitions across plants; failure coding completeness ≥95 %.
