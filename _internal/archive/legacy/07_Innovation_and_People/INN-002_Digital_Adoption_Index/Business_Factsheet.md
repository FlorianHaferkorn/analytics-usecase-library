---
id: "INN-002"
title: "Digital Adoption Index"
domain: "Innovation & People"
owner: "Head of Digital Transformation / CIO"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Digital Adoption Rate %", "Automation Rate %"]
supports_strategic_kpi_ids: ["people.digital_adoption.pct"]
action_codes: ["I3"]
expected_impact: "+5 pp Adoption durch gezieltes Change- und Enablement-Management."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit>Department",
  "Process.Area>Subprocess",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Process Area: All"
]
qa_asserts: ["RI_OK", "UsageEvents_Tracked"]
required_kpi_ids: [
  "people.digital_adoption.pct"
]
required_kpis:
  people.digital_adoption.pct: "Digital Adoption Rate %"
data_requirements:
  facts:
    - name: fact_digital_usage
      grain: process_user_day
      primary_key: [UserID, ProcessID, UsageDate]
      required_columns:
        - { name: UserID, type: string, role: attribute }
        - { name: ProcessID, type: string, role: attribute }
        - { name: UsageDate, type: date, role: date_key }
        - { name: IsDigital, type: bool, role: indicator }
        - { name: TransactionsCount, type: int, role: amount }
    - name: fact_process_baseline
      grain: process
      primary_key: [ProcessID]
      required_columns:
        - { name: IsEligibleForDigital, type: bool, role: indicator }
  dims:
    - name: dim_process
      grain: process
      primary_key: [ProcessID]
      required_columns:
        - { name: ProcessArea, type: string }
        - { name: Subprocess, type: string }
model_mapping:
  "Process": "dim_process[ProcessID]"
  "Transactions Count": "fact_digital_usage[TransactionsCount]"
  "Is Digital Flag": "fact_digital_usage[IsDigital]"
---

# INN-002 Digital Adoption Index - Business Factsheet

## 1. Summary
- **Business Goal:** Track how quickly business units adopt digital workflows to reduce manual effort, errors, and cycle time.
- **Target Audience:** Chief Digital Officer, Transformation leads, Process owners, IT product managers.
- **Business Priority:** High for scaling automation investments and ensuring ROI.
- **Expected Impact:** +5 pp digital adoption rate and reduced manual workload through targeted change and enablement programs.

## 2. Core Questions
- What is the Digital Adoption Rate % by process, org, and time period, and where do gaps persist?
- Which user groups still execute predominantly manual transactions and why?
- How does adoption correlate with efficiency metrics (cycle time, error rate, backlog)?
- Which interventions (training, UX fixes, automation) deliver the highest adoption gains?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Digital Adoption Rate % | Core KPI measuring shift to digital workflows. | Digital transactions / total eligible transactions for a process/org/time slice. | Target typically >80 % for mature processes; <60 % requires action. | Guides prioritization of change and funding. |
| Automation Rate % | Shows share of transactions auto-executed without manual touch. | Fully automated transactions / total transactions. | Low rate indicates potential for RPA or workflow automation. | Supports investment cases. |
| Manual Effort Hours | Quantifies remaining manual workload. | Estimated hours spent on manual transactions (transactions * standard handling time). | Helps size savings from automation waves. | Inputs into ROI calculations. |
| Adoption Trend (pp) | Monitors improvement velocity. | Period-over-period change in adoption %. | Negative trend signals change fatigue. | Helps schedule additional enablement. |

## 4. Business Logic & Thresholds
- Processes flagged as eligible for digital must come from the process baseline; others excluded from KPI denominator.
- Adoption measured on rolling 3-month view for executive dashboard; weekly view used by process teams.
- Manual effort hours use standardized handling time per process maintained in reference table; updates require governance approval.
- Action code I3 triggered when adoption < target for two consecutive months or declines >5 pp quarter-over-quarter.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| I3 | Digital Adoption Boost | Targeted change, UX, training, and automation fixes to raise adoption. | Adoption < target or negative trend >5 pp. | +5 pp adoption within quarter; manual effort -10 %. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Digital Adoption Rate %, Automation Rate %, Manual Effort Hours, and trend delta.
- Alert banner for processes below target with link to action code status.

### 6.2 30-Second Layer (Story)
- Heatmap Org Region > Process Area with adoption % and automation %.
- Trend lines (12 months) for top processes vs target.
- Waterfall showing drivers of adoption change (user growth, UX fix, automation release).

### 6.3 300-Second Layer (Detail)
- Drillable table Process Area > Subprocess > Action Owner with KPIs, blockers, open tasks.
- User cohort view (role, region) showing adoption distribution and manual effort.
- Export-ready dataset for change managers to contact non-adopters.

## 7. Dependencies & Constraints
- Usage tracking (digital vs manual) must be logged per transaction with unique process IDs.
- Eligibility list maintained in process baseline; includes automation potential and handling time.
- User master data links usage events to org hierarchy and personas for targeted interventions.
- Latency <= 24 hours to support weekly standups; data gaps flagged automatically.

## 8. Success Criteria
- Leading: 95 % of priority processes monitored weekly; action code I3 opened within 3 days of breach.
- Lagging: +5 pp adoption rate in targeted processes and 10 % reduction in manual effort hours within quarter.