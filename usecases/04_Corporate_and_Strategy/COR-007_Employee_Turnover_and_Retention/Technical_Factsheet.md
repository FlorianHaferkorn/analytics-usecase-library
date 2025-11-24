# Employee Turnover & Retention - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_headcount_movement
  grain: employee_month
  primary_key:
  - EmployeeID
  - Month
  required_columns:
  - name: EmployeeID
    type: string
    role: attribute
  - name: Month
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: FunctionID
    type: string
    role: attribute
  - name: Status
    type: string
    role: status
  - name: Entry Date
    type: date
    role: helper
  - name: Exit Date
    type: date
    role: helper
  - name: Absence Hours
    type: decimal
    role: helper
  - name: Work Hours
    type: decimal
    role: helper
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Country
    type: string
  - name: BusinessUnit
    type: string
- name: dim_function
  grain: function
  primary_key:
  - FunctionID
  required_columns:
  - name: FunctionName
    type: string
  - name: Department
    type: string
- name: dim_employee
  grain: employee
  primary_key:
  - EmployeeID
  required_columns:
  - name: TenureBand
    type: string
  - name: Seniority
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
  required_columns:
  - name: Year
    type: int
  - name: Month
    type: int
relationships:
- from: fact_headcount_movement.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_headcount_movement.FunctionID
  to: dim_function.FunctionID
  cardinality: many-to-one
  direction: single
- from: fact_headcount_movement.EmployeeID
  to: dim_employee.EmployeeID
  cardinality: many-to-one
  direction: single
- from: fact_headcount_movement.Month
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
- Employee Turnover % (ID: hr.turnover.pct)
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
- Employee ID -> dim_employee[EmployeeID]
- Status -> fact_headcount_movement[Status]
- Absence Hours -> fact_headcount_movement[Absence Hours]
- Work Hours -> fact_headcount_movement[Work Hours]
- Org -> dim_org[OrgID]
- Function -> dim_function[FunctionID]
- Date -> dim_date[Date]
