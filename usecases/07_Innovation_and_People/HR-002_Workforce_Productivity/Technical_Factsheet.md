# HR-002 Workforce Productivity - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_employee
    grain: employee
    columns:
      - {name: EmployeeID, type: text, role: primary_key}
      - {name: Department, type: text}
      - {name: Role, type: text}
      - {name: Level, type: text}
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
  - name: fact_hr_headcount
    grain: employee_month
    primary_key:
      - EmployeeID
      - SnapshotMonth
    columns:
      - {name: EmployeeID, type: text, role: employee_key, ref: dim_employee}
      - {name: SnapshotMonth, type: date_key, ref: dim_date}
      - {name: FTE, type: decimal, role: amount}
      - {name: ScheduledHours, type: decimal, role: amount}
      - {name: AbsentHours, type: decimal, role: amount}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
  - name: fact_financials
    grain: org_month
    primary_key:
      - OrgID
      - Month
    columns:
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: RevenueAmount, type: decimal, role: amount}
      - {name: GrossMarginAmount, type: decimal, role: amount}
      - {name: PersonnelCostAmount, type: decimal, role: amount}
relationships:
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
  - from: fact_financials.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_financials.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Dataset: Contoso Sales Sample for Power BI Desktop.SemanticModel (Innovation and People workspace) with cross-domain finance link.
- Facts act_hr_headcount and act_financials stored in same model to avoid composite models; shared dim_org and dim_date ensure alignment with finance KPIs.
- Relationship directions kept single; avoid bi-directional filters to maintain predictable DAX.
- Sort-by columns: DepartmentSort, RoleSort, LevelSort maintained in dim_employee; BusinessUnitSort in dim_org.
- Hidden technical fields: Employee personal data, payroll IDs, and currency conversion factors remain hidden but available for QA.
- Hierarchies: Org Region > Business Unit > Department; Employee Role > Level; Date Year > Quarter > Month.

## 3. Measures (DAX + Description)
`
Revenue Amount =
    // TODO: Provide DAX via Power BI MCP summing fact_financials[RevenueAmount]
`
Description:
  Purpose: Base revenue measure for productivity ratios.
  Definition: Sum of RevenueAmount respecting filters.
  Grain & Scope: Org-month aggregated.
  Unit/Format: Currency (0 decimals).
  Lineage: fact_financials[RevenueAmount].
  QA: Tie out vs finance close pack (variance <= 0.3 %).

`
Average FTE =
    // TODO: Provide DAX via Power BI MCP averaging fact_hr_headcount[FTE] across SnapshotMonth
`
Description:
  Purpose: Denominator for productivity measures.
  Definition: Average FTE for selected context and time frame.
  Grain & Scope: Employee-month aggregated.
  Unit/Format: Decimal (2 decimals).
  Lineage: fact_hr_headcount[FTE].
  QA: Compare vs HR headcount cube; tolerance 0.2 %.

`
Revenue per FTE =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Revenue Amount], [Average FTE])
`
Description:
  Purpose: Core productivity KPI.
  Definition: Revenue Amount divided by Average FTE; handles zero denominators with DIVIDE.
  Grain & Scope: Aggregates to any org level.
  Unit/Format: Currency 0 decimals.
  Lineage: Revenue Amount, Average FTE.
  QA: Reconcile sample vs manual calculation.

`
Gross Margin per FTE =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Gross Margin Amount], [Average FTE])
`
Description:
  Purpose: Profit productivity KPI.
  Definition: Gross Margin / Average FTE.
  Unit/Format: Currency 0 decimals.
  Lineage: fact_financials[GrossMarginAmount], Average FTE.
  QA: +/- 0.3 % vs finance workbook.

`
Personnel Cost Ratio % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Personnel Cost Amount], [Revenue Amount])
`
Description:
  Purpose: Tracks workforce cost vs revenue.
  Definition: Personnel costs divided by revenue.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_financials[PersonnelCostAmount], Revenue Amount.
  QA: Must equal finance KPI deck.

`
Absenteeism % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Absent Hours], [Scheduled Hours])
`
Description:
  Purpose: Availability KPI.
  Definition: Absent hours divided by scheduled hours.
  Unit/Format: Percentage with 1 decimal.
  Lineage: fact_hr_headcount[AbsentHours], fact_hr_headcount[ScheduledHours].
  QA: Compare vs HR absence report.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Revenue Amount | Sum, Currency 0 | Display folder: 02_Productivity |
| Gross Margin Amount | Sum, Currency 0 | Display folder: 02_Productivity |
| Personnel Cost Amount | Sum, Currency 0 | Display folder: 02_Productivity |
| Average FTE | Average, Decimal 2 | Display folder: 01_Workforce |
| Revenue per FTE | No summarization, Currency 0 | Display folder: 02_Productivity |
| Gross Margin per FTE | No summarization, Currency 0 | Display folder: 02_Productivity |
| Personnel Cost Ratio % | No summarization, Percentage 1 | Display folder: 02_Productivity |
| Absenteeism % | No summarization, Percentage 1 | Display folder: 01_Workforce |
| Org hierarchy fields | Do not summarize | Provide drill path Region > Business Unit > Department |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline KPIs | Revenue per FTE, Gross Margin per FTE, Personnel Cost Ratio %, Absenteeism % | Include plan/LY references and thresholds |
| Line Chart | Trend KPIs | Date hierarchy, Revenue per FTE, Absenteeism % | Rolling 24 months |
| Variance Waterfall | Explain Personnel Cost Ratio % | Revenue, Personnel Costs, mix drivers | Needs custom calc table |
| Tree Map | Productivity by org | Org hierarchy, Revenue per FTE | Conditional coloring by variance |
| Detail Table | Action tracking | Department, Role, KPIs, Action Code | Include drill-through to absence details |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh (SnapshotMonth rolling 36M; Month rolling 36M) to limit dataset size.
- Partition facts by Month; ensure Power Query filters fold to source.
- Refresh cadence: daily after HR & Finance close (02:30 CET) with manual refresh allowed for month-end adjustments.
- Monitor dataset size; consider aggregation table for >36M history if needed.

## 7. RLS/OLS Requirements
- Role HR_Global: unrestricted view for HR leadership.
- Role Org_Manager: filter dim_org[OrgID] via security mapping table referencing USERPRINCIPALNAME().
- Role Department_Lead: filter dim_employee[Department] similarly; prevents cross-department visibility.
- Finance-only fields (PersonnelCostAmount) optionally hidden for non-authorized roles via object-level security.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_hr_headcount -> dim_employee/dim_org/dim_date | >= 99.7 % matches | 0.3 % |
| Referential Integrity | fact_financials -> dim_org/dim_date | >= 99.9 % matches | 0.1 % |
| Hours_Reconcile | Scheduled vs Absent Hours | ScheduledHours >= AbsentHours; negative values blocked | Hard fail |
| Headcount_Consistent | Average FTE vs HR cube | Variance <= 0.2 % | 0.2 % |
| Finance_Revenue_TieOut | Revenue Amount | Must match finance ledger at reporting level | +/- 0.3 % |
