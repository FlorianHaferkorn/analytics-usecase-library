# HR-001 Employee Development and Learning - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_employee
    grain: employee
    columns:
      - {name: EmployeeID, type: text, role: primary_key}
      - {name: Department, type: text, role: attribute}
      - {name: Role, type: text, role: attribute}
      - {name: Level, type: text, role: attribute}
  - name: dim_org
    grain: org
    columns:
      - {name: OrgID, type: text, role: primary_key}
      - {name: Region, type: text}
      - {name: BusinessUnit, type: text}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
fact:
  - name: fact_hr_training
    grain: employee_session
    columns:
      - {name: EmployeeID, type: text, role: employee_key, ref: dim_employee}
      - {name: SessionDate, type: date_key, ref: dim_date}
      - {name: TrainingHours, type: decimal, role: amount}
      - {name: TrainingType, type: text, role: attribute}
      - {name: TrainingCategory, type: text, role: attribute}
      - {name: MandatoryFlag, type: boolean, role: indicator}
  - name: fact_hr_headcount
    grain: employee_month
    columns:
      - {name: EmployeeID, type: text, role: employee_key, ref: dim_employee}
      - {name: SnapshotMonth, type: date_key, ref: dim_date}
      - {name: FTE, type: decimal, role: amount}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
relationships:
  - from: fact_hr_training.EmployeeID
    to: dim_employee.EmployeeID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_hr_training.SessionDate
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_hr_headcount.EmployeeID
    to: dim_employee.EmployeeID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_hr_headcount.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_hr_headcount.SnapshotMonth
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Semantic model: Contoso Sales Sample for Power BI Desktop.SemanticModel (Innovation and People workspace) with shared dimensions for HR reporting.
- Facts loaded via HR dataflow; training sessions refreshed daily, headcount monthly snapshot with effective dating.
- Relationship directions kept single to simplify row-level security by org and role; avoid bi-directional filters.
- Conformed Date/Org dimensions reused across other HR use cases for drill-through consistency.
- Sort-by columns: Department sorted by DepartmentOrder, Role by RoleSort; Level uses numeric seniority index.
- Hidden helper fields: MandatoryFlag raw column, SessionID, ingestion timestamps for audit trace.
- Hierarchies required: Org Region > Business Unit > Department, Employee Role > Level, Date Year > Quarter > Month.

## 3. Measures (DAX + Description)
`
Training Hours =
    // TODO: Provide DAX via Power BI MCP summing fact_hr_training[TrainingHours]
`
Description:
  Purpose: Base measure for learning intensity.
  Definition: Sum of TrainingHours respecting filters.
  Grain & Scope: Employee session aggregated to slice level.
  Unit/Format: Decimal hours (1 decimal).
  Lineage: fact_hr_training[TrainingHours].
  QA: Reconcile vs LMS export (variance <= 0.5 %).

`
Training Hours per FTE =
    // TODO: Provide DAX via Power BI MCP dividing Training Hours by Average FTE using DIVIDE
`
Description:
  Purpose: Core KPI for activity per employee.
  Definition: Training Hours divided by average FTE for same context.
  Grain & Scope: Aggregates to any org, department, or role level.
  Unit/Format: Decimal hours (1 decimal).
  Lineage: fact_hr_training[TrainingHours], fact_hr_headcount[FTE].
  QA: Compare vs manual calculation for sample departments.

`
Training Coverage % =
    // TODO: Provide DAX via Power BI MCP calculating learners completing mandatory courses divided by eligible FTE
`
Description:
  Purpose: Compliance indicator for mandatory programs.
  Definition: Distinct employees completing mandatory trainings / eligible employees.
  Grain & Scope: Period-based ratio.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_hr_training[MandatoryFlag], dim_employee attributes.
  QA: Align with compliance attestations; tolerance +/- 1 pp.

`
Revenue per FTE =
    // TODO: Provide DAX via Power BI MCP referencing shared finance measure divided by headcount
`
Description:
  Purpose: Productivity proxy linked to finance cube.
  Definition: Net revenue amount (linked measure) divided by average FTE.
  Grain & Scope: Org-level aggregated.
  Unit/Format: Currency with 0 decimals.
  Lineage: Finance semantic model bridge + fact_hr_headcount[FTE].
  QA: Must reconcile with finance KPI deck (variance <= 0.5 %).

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Training Hours | Sum, Decimal 1 | Display folder: 01_Learning |
| Training Hours per FTE | No summarization, Decimal 1 | Display folder: 01_Learning |
| Training Coverage % | No summarization, Percentage 1 | Display folder: 01_Learning |
| Revenue per FTE | Sum, Currency 0 | Display folder: 02_Productivity |
| Department / Role / Level | Do not summarize | Maintain hierarchy order |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Show primary KPIs vs target | Training Hours per FTE, Training Coverage %, Revenue per FTE | Add goal values from parameter table |
| Trend Line | Monitor KPI evolution | Date hierarchy, KPIs | Rolling 12-24 months; include plan/benchmark lines |
| Tree Map | Identify gaps by org | Org hierarchy, Training Hours per FTE | Conditional color by threshold |
| Scatter Plot | Correlate learning vs productivity | Training Hours per FTE (X), Revenue per FTE (Y), bubble size = FTE | Enable play axis for time |
| Detail Table | Compliance tracking | Employee attributes, Mandatory completion flag, Action code | Use row-level tooltips for aging |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh on SessionDate (rolling 24 months) and SnapshotMonth (rolling 36 months).
- Partition training fact by SessionDate month; leverage dataflow parameters to fold filters.
- Refresh cadence: LMS data nightly at 02:00 CET, dataset refresh 02:30 CET; headcount snapshots monthly but reprocessed nightly for corrections.
- Monitor dataset size; consider aggregations for historic >24M to keep below capacity.

## 7. RLS/OLS Requirements
- Role HR_Global: unrestricted view for HR leadership.
- Role Org_Manager: filter dim_org[OrgID] using bridge table mapping manager UPNs.
- Role Department_Lead: filter dim_employee[Department] via mapping table; ensures managers only see their teams.
- Sensitive personal attributes (e.g., employee names) hidden unless user is in HR_Global.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_hr_training -> dim_employee/dim_date | >= 99.7 % match | 0.3 % |
| TrainingHours_Reconcile | Training Hours measure | Sum vs LMS export difference <= 0.5 % | 0.5 % |
| Headcount_Consistent | FTE vs HR cube | Dataset FTE equals headcount cube within 0.2 % | 0.2 % |
| RI_OK | fact_hr_headcount -> dim_org | No orphan OrgID rows | Hard fail |
