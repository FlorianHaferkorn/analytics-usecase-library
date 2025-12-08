# Workforce Productivity & Turnover Analysis - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_hr_headcount
  grain: employee_month
  primary_key:
  - EmployeeID
  - SnapshotMonth
  required_columns:
  - name: EmployeeID
    type: string
    role: employee_key
  - name: SnapshotMonth
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Department
    type: string
    role: attribute
  - name: Function
    type: string
    role: attribute
  - name: Country
    type: string
    role: attribute
  - name: FTEFactor
    type: decimal
    role: helper
  - name: ContractType
    type: string
    role: attribute
  - name: HireDate
    type: date
    role: helper
  - name: LeaveDate
    type: date
    role: helper
- name: fact_hr_cost
  grain: employee_month
  primary_key:
  - EmployeeID
  - SnapshotMonth
  required_columns:
  - name: PersonnelCost
    type: decimal
    role: amount
  - name: BonusCost
    type: decimal
    role: amount
  - name: OvertimeCost
    type: decimal
    role: amount
- name: fact_financials
  grain: org_month
  primary_key:
  - OrgID
  - SnapshotMonth
  required_columns:
  - name: RevenueAmount
    type: decimal
    role: amount
  - name: GrossMarginAmount
    type: decimal
    role: amount
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: BusinessUnit
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_hr_headcount.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_hr_headcount.SnapshotMonth
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_hr_cost.EmployeeID
  to: fact_hr_headcount.EmployeeID
  cardinality: many-to-one
  direction: single
- from: fact_financials.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_financials.SnapshotMonth
  to: dim_date.Date
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
- Revenue per FTE (ID: hr.revenue_per_fte.amount)
- Gross Margin per FTE (ID: hr.gm_per_fte.amount)
- Personnel Cost Ratio % (ID: hr.personnel_cost_ratio.pct)
- Turnover Rate % (ID: hr.turnover.pct)
- Absenteeism % (ID: hr.absenteeism.pct)

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
- Headcount_Positive
- Turnover_Range

## 9. Model Mapping Reference
- Employee -> fact_hr_headcount[EmployeeID]
- Region -> dim_org[Region]
- Department -> fact_hr_headcount[Department]
- FTE -> fact_hr_headcount[FTEFactor]
- Personnel Cost -> fact_hr_cost[PersonnelCost]
- Revenue Amount -> fact_financials[RevenueAmount]
- Gross Margin Amount -> fact_financials[GrossMarginAmount]
- Snapshot Month -> fact_hr_headcount[SnapshotMonth]
