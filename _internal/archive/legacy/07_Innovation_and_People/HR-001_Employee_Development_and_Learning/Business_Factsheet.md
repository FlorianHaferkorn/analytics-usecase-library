---
id: "HR-001"
title: "Employee Development & Learning"
domain: "Corporate and Strategy"
owner: "Head of HR / Learning & Development"
impact: "Medium"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Employee Engagement %", "Productivity per FTE"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "people.training_hours.amount"]
action_codes: ["H1", "H2"]
expected_impact: "+0.5 pp Productivity, +3 pp Engagement durch gezielte TrainingsmaÃƒÅ¸nahmen."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit>Department",
  "Employee.Role>Level",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Department: All"
]
qa_asserts: ["RI_OK", "TrainingHours_Reconcile", "Headcount_Consistent"]
required_kpi_ids: [
  "people.training_hours.amount",
  "hr.revenue_per_fte.amount"
]
required_kpis:
  people.training_hours.amount: "Training Hours"
  hr.revenue_per_fte.amount: "Revenue per FTE"
data_requirements:
  facts:
    - name: fact_hr_training
      grain: employee_session
      primary_key: [EmployeeID, TrainingID, SessionDate]
      required_columns:
        - { name: EmployeeID, type: string, role: employee_key }
        - { name: SessionDate, type: date, role: date_key }
        - { name: TrainingHours, type: decimal, role: amount }
        - { name: TrainingType, type: string, role: attribute }
    - name: fact_hr_headcount
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: FTE, type: decimal, role: amount }
        - { name: OrgID, type: string, role: org_key }
  dims:
    - name: dim_employee
      grain: employee
      primary_key: [EmployeeID]
      required_columns:
        - { name: Department, type: string }
        - { name: Role, type: string }
        - { name: Level, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_hr_training.EmployeeID, to: dim_employee.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_hr_training.SessionDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_hr_headcount.EmployeeID, to: dim_employee.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_hr_headcount.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
model_mapping:
  "Training Hours": "fact_hr_training[TrainingHours]"
  "FTE": "fact_hr_headcount[FTE]"
---

# HR-001 Employee Development and Learning - Business Factsheet

## 1. Summary
- **Business Goal:** Increase workforce productivity and engagement by aligning training supply with strategic capability gaps and tracking outcomes.
- **Target Audience:** CHRO, Learning and Development leaders, HR business partners, department heads.
- **Business Priority:** Medium (continuous improvement program with quarterly steering).
- **Expected Impact:** +0.5 pp productivity per FTE and +3 pp employee engagement via targeted upskilling.

## 2. Core Questions
- Are training hours per FTE on target across regions, departments, and role levels?
- Which populations have low training coverage or overdue mandatory courses?
- Does higher training intensity correlate with productivity or revenue per FTE improvements?
- Where should budgets or course capacity be reallocated to close skill gaps fastest?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Training Hours per FTE | Primary activity KPI for learning intensity. | Total delivered training hours within the selected period divided by average FTE (no DAX wording). | Target band depends on role: e.g., 12-20 h per quarter; <10 h signals underinvestment. | Drives budget allocation, course capacity planning, and compliance with learning targets. |
| Training Coverage % | Measures reach of mandatory or strategic programs. | Share of active employees that completed required trainings in the selected period. | <85 % coverage on mandatory programs triggers escalation. | Determines risk exposure (audit, safety) and informs action code H2. |
| Revenue per FTE | Proxy for productivity uplift from learning initiatives. | Net revenue attributed to a business unit divided by average FTE. | Sustained increase after training rollout validates program effectiveness. | Used to justify investment and prioritize future curricula. |

## 4. Business Logic & Thresholds
- Coverage below 85 % for mandatory curricula triggers action code H2; <70 % escalates to executive review.
- Training Hours per FTE <10 h for two consecutive quarters indicates risk of skill erosion and prompts action code H1.
- Productivity improvements are measured over a rolling 3-quarter window to smooth hiring effects.
- All KPIs evaluated at Org Region > Business Unit > Department and Employee Role > Level hierarchies.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| H1 | Learning Path Optimization | Re-prioritize courses, launch targeted cohorts, and reallocate budget toward under-trained segments. | Training Hours per FTE <10 h or productivity lag vs peer units. | +3-5 h per FTE in targeted segment; productivity delta closes within 2 quarters. |
| H2 | Mandatory Training Campaign | Coordinate communications, manager follow-up, and system nudges to reach compliance thresholds. | Training Coverage % <85 % for regulatory or safety topics. | Coverage returns to >95 % within one cycle; audit readiness maintained. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Training Hours per FTE, Training Coverage %, Revenue per FTE, and progress vs target.
- Alert banner for segments breaching compliance thresholds.

### 6.2 30-Second Layer (Story)
- Trend lines (12-24 months) for each KPI with annotations for program launches.
- Tree map Org Region > Business Unit showing distribution of training hours.
- Scatter plot comparing Training Hours per FTE vs Revenue per FTE to highlight correlations.

### 6.3 300-Second Layer (Detail)
- Drillable matrix Employee Role > Level with KPI set plus action code status.
- Table of mandatory courses with coverage %, aging, and owner notes.
- Export-ready dataset of individual sessions for audit sampling.

## 7. Dependencies & Constraints
- Learning Management System must provide daily snapshots with employee IDs aligned to HR master data.
- FTE calculations sourced from the official headcount cube; partial FTEs must be included to avoid overstatement.
- Training taxonomy (type, modality, mandatory flag) maintained centrally to ensure consistent aggregation.
- Data latency <= 24 hours to support weekly steering; historical restatements documented via change log.

## 8. Success Criteria
- Leading indicators: 90 % of business units review the dashboard monthly; >80 % of targeted learners enroll in new programs within 30 days.
- Lagging indicators: Training Coverage % >= 95 % on mandatory tracks; +0.5 pp productivity per FTE and +3 pp engagement by fiscal year end.