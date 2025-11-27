---
id: "COR-001"
title: "Project ROI & Benefit Tracking"
domain: "Corporate and Strategy"
owner: "Head of Strategy / PMO / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Project ROI %", "Benefit Realization %", "Operating Cost Ratio %"]
supports_strategic_kpi_ids: ["corp.project.roi.pct", "corp.benefit.realization.pct", "corp.payback.months"]
action_codes: ["SP1", "SP2", "O2", "O3", "SP3"]
expected_impact: "+5-10 pp realized ROI; +15 % benefit realization; -10-20 % manual reporting effort"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Portfolio.Pillar>Program>Project",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Portfolio: All",
  "Stage: All"
]
qa_asserts: ["RI_OK", "Benefit_Not_Negative", "ROI_InRange"]
required_kpi_ids: [
  "corp.project.roi.pct",
  "corp.benefit.realization.pct",
  "corp.budget.adherence.pct",
  "corp.schedule.adherence.pct",
  "corp.payback.months"
]
required_kpis:
  corp.project.roi.pct: "Project ROI %"
  corp.benefit.realization.pct: "Benefit Realization %"
  corp.budget.adherence.pct: "Budget Adherence %"
  corp.schedule.adherence.pct: "Schedule Adherence %"
  corp.payback.months: "Payback Period (Months)"
data_requirements:
  facts:
    - name: fact_projects
      grain: project_month
      primary_key: [ProjectID, SnapshotMonth]
      required_columns:
        - { name: ProjectID, type: string, role: project_key }
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: Portfolio, type: string, role: attribute }
        - { name: Pillar, type: string, role: attribute }
        - { name: Stage, type: string, role: status }
        - { name: PlannedCost, type: decimal, role: amount }
        - { name: ActualCost, type: decimal, role: amount }
        - { name: PlannedBenefit, type: decimal, role: amount }
        - { name: RealizedBenefit, type: decimal, role: amount }
        - { name: ExpectedPaybackMonths, type: decimal, role: helper }
        - { name: ScheduleProgressPct, type: decimal, role: helper }
    - name: fact_project_actions
      grain: action
      primary_key: [ProjectID, ActionID]
      required_columns:
        - { name: ActionDate, type: date, role: date_key }
        - { name: ActionType, type: string, role: attribute }
        - { name: Owner, type: string, role: attribute }
  dims:
    - name: dim_project
      grain: project
      primary_key: [ProjectID]
      required_columns:
        - { name: ProjectName, type: string }
        - { name: Sponsor, type: string }
        - { name: BusinessOwner, type: string }
        - { name: CapexOpexFlag, type: string }
        - { name: RiskLevel, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_projects.ProjectID, to: dim_project.ProjectID, cardinality: many-to-one, direction: single }
    - { from: fact_projects.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_project_actions.ProjectID, to: dim_project.ProjectID, cardinality: many-to-one, direction: single }
model_mapping:
  "Project": "dim_project[ProjectName]"
  "Portfolio": "fact_projects[Portfolio]"
  "Pillar": "fact_projects[Pillar]"
  "Stage": "fact_projects[Stage]"
  "Planned Cost": "fact_projects[PlannedCost]"
  "Actual Cost": "fact_projects[ActualCost]"
  "Planned Benefit": "fact_projects[PlannedBenefit]"
  "Realized Benefit": "fact_projects[RealizedBenefit]"
  "Schedule Progress %": "fact_projects[ScheduleProgressPct]"
  "Snapshot Month": "fact_projects[SnapshotMonth]"
---

# Project ROI & Benefit Tracking - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure transparency on project performance by tracking realized financial and non-financial benefits versus investment cost - enabling data-driven portfolio steering, reprioritization, and early escalation.

---
- **Target Audience:** Head of Strategy / PMO / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** +5-10 pp realized ROI; +15 % benefit realization; -10-20 % manual reporting effort

## 2. Core Questions
- What is the realized ROI per project and portfolio segment?
- Are projects delivering expected benefits on time and within budget?
- Which initiatives drive the highest strategic and financial impact?
- What portion of planned savings or revenue uplift is actually realized?
- How do project delays correlate with ROI erosion?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Project ROI %, Benefit Realization %, Budget Adherence %, Schedule Adherence %, Payback Period (Months) with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a