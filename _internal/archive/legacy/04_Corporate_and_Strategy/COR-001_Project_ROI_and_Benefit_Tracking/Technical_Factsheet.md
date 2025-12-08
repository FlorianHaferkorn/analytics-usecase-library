# Project ROI & Benefit Tracking - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_projects
  grain: project_month
  primary_key:
  - ProjectID
  - SnapshotMonth
  required_columns:
  - name: ProjectID
    type: string
    role: project_key
  - name: SnapshotMonth
    type: date
    role: date_key
  - name: Portfolio
    type: string
    role: attribute
  - name: Pillar
    type: string
    role: attribute
  - name: Stage
    type: string
    role: status
  - name: PlannedCost
    type: decimal
    role: amount
  - name: ActualCost
    type: decimal
    role: amount
  - name: PlannedBenefit
    type: decimal
    role: amount
  - name: RealizedBenefit
    type: decimal
    role: amount
  - name: ExpectedPaybackMonths
    type: decimal
    role: helper
  - name: ScheduleProgressPct
    type: decimal
    role: helper
- name: fact_project_actions
  grain: action
  primary_key:
  - ProjectID
  - ActionID
  required_columns:
  - name: ActionDate
    type: date
    role: date_key
  - name: ActionType
    type: string
    role: attribute
  - name: Owner
    type: string
    role: attribute
dims:
- name: dim_project
  grain: project
  primary_key:
  - ProjectID
  required_columns:
  - name: ProjectName
    type: string
  - name: Sponsor
    type: string
  - name: BusinessOwner
    type: string
  - name: CapexOpexFlag
    type: string
  - name: RiskLevel
    type: string
- name: dim_org
  grain: org
  primary_key:
  - OrgID
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_projects.ProjectID
  to: dim_project.ProjectID
  cardinality: many-to-one
  direction: single
- from: fact_projects.SnapshotMonth
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_project_actions.ProjectID
  to: dim_project.ProjectID
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required facts/dims per contract above.
- Ensure relationships are single-direction many-to-one (role-playing dates if needed).
- Provide conformed Org/Product/Initiative hierarchies.

## 3. Measures (DAX + Description)
Following KPIs require measures (DAX delivered separately):
- Project ROI % (ID: corp.project.roi.pct)
- Benefit Realization % (ID: corp.benefit.realization.pct)
- Budget Adherence % (ID: corp.budget.adherence.pct)
- Schedule Adherence % (ID: corp.schedule.adherence.pct)
- Payback Period (Months) (ID: corp.payback.months)

## 4. Defaults & Formatting
- Apply correct format strings (currency, %, integer).
- Use display folders (01_Strategic, 02_Variance, etc.).
- Set data categories for Org/Initiative/Timeline fields.

## 5. Visual / Interaction Requirements
- Map visuals (cards, bridges, funnels) to required fields.
- Define drill paths for Org, Initiative, Time.
- Specify tooltip fields and sort-by logic.

## 6. Performance & Refresh
- Storage mode: Import (unless monthly snapshot suggests Hybrid).
- Refresh cadence aligned with corporate close cadence.
- Partitioning by FiscalPeriod where data volume is high.

## 7. RLS/OLS Requirements
- Org-based RLS (Region/Entity).
- Optional Initiative-based restrictions for project owners.

## 8. QA & Validation Rules
- RI_OK
- Benefit_Not_Negative
- ROI_InRange

## 9. Model Mapping Reference
- Project -> dim_project[ProjectName]
- Portfolio -> fact_projects[Portfolio]
- Pillar -> fact_projects[Pillar]
- Stage -> fact_projects[Stage]
- Planned Cost -> fact_projects[PlannedCost]
- Actual Cost -> fact_projects[ActualCost]
- Planned Benefit -> fact_projects[PlannedBenefit]
- Realized Benefit -> fact_projects[RealizedBenefit]
- Schedule Progress % -> fact_projects[ScheduleProgressPct]
- Snapshot Month -> fact_projects[SnapshotMonth]
