---
id: "COR-007"
title: "Employee Turnover & Retention"
domain: "Corporate and Strategy"
owner: "Head of HR / People Analytics"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Employee Turnover %", "Employee Engagement %"]
supports_strategic_kpi_ids: ["hr.turnover.pct", "people.engagement.index"]
action_codes: ["C1", "SP1", "O2"]
expected_impact: "-1â€“2 pp turnover; higher engagement and lower recruiting cost."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>BusinessUnit",
  "Workforce.Function>Department",
  "Employee.Seniority>Tenure",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Function: All"
]
qa_asserts: ["RI_OK", "Headcount_Positive", "Turnover_Range"]
required_kpi_ids: [
  "hr.turnover.pct",
  "hr.absenteeism.pct"
]
required_kpis:
  hr.turnover.pct: "Employee Turnover %"
  hr.absenteeism.pct: "Absenteeism %"
data_requirements:
  facts:
    - name: fact_headcount_movement
      grain: employee_month
      primary_key: [EmployeeID, Month]
      required_columns:
        - { name: EmployeeID, type: string, role: attribute }
        - { name: Month, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: FunctionID, type: string, role: attribute }
        - { name: "Status", type: string, role: status }
        - { name: "Entry Date", type: date, role: helper }
        - { name: "Exit Date", type: date, role: helper }
        - { name: "Absence Hours", type: decimal, role: helper }
        - { name: "Work Hours", type: decimal, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_function
      grain: function
      primary_key: [FunctionID]
      required_columns:
        - { name: FunctionName, type: string }
        - { name: Department, type: string }
    - name: dim_employee
      grain: employee
      primary_key: [EmployeeID]
      required_columns:
        - { name: TenureBand, type: string }
        - { name: Seniority, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_headcount_movement.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_headcount_movement.FunctionID, to: dim_function.FunctionID, cardinality: many-to-one, direction: single }
    - { from: fact_headcount_movement.EmployeeID, to: dim_employee.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_headcount_movement.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Employee ID": "dim_employee[EmployeeID]"
  "Status": "fact_headcount_movement[Status]"
  "Absence Hours": "fact_headcount_movement[Absence Hours]"
  "Work Hours": "fact_headcount_movement[Work Hours]"
  "Org": "dim_org[OrgID]"
  "Function": "dim_function[FunctionID]"
  "Date": "dim_date[Date]"
---

# Employee Turnover & Retention - Business Factsheet

## 1. Summary
- **Business Goal:** Monitor and improve employee turnover and retention across regions and functions, and identify hotspots that require targeted HR interventions.

---
- **Target Audience:** Head of HR / People Analytics
- **Business Priority:** High
- **Expected Impact:** -1"2 pp turnover; higher engagement and lower recruiting cost.

## 2. Core Questions
- What is our turnover rate by region, business unit, function, and tenure band?
- Where do we see unusually high or low turnover, and what patterns are associated (tenure, seniority, function)?
- How does absenteeism correlate with turnover and retention?
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
- KPI cards for Employee Turnover %, Absenteeism % with Plan/LY deltas.
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