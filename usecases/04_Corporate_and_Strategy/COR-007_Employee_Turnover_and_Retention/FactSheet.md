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
expected_impact: "-1–2 pp turnover; higher engagement and lower recruiting cost."
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

# Employee Turnover & Retention

## 1. Business Goal
Monitor and improve employee turnover and retention across regions and functions, and identify hotspots that require targeted HR interventions.

---

## 2. Business Context
High employee turnover drives recruitment cost, knowledge loss, and productivity issues.  
Without a consistent measurement framework, it is hard to compare turnover across units or link it to engagement and performance.  
This Use Case standardizes turnover and absenteeism KPIs and provides a segmented view.

---

## 3. Key Questions
- What is our turnover rate by region, business unit, function, and tenure band?
- Where do we see unusually high or low turnover, and what patterns are associated (tenure, seniority, function)?
- How does absenteeism correlate with turnover and retention?

---

## 4. Key KPIs
| KPI             | Definition                                          | Unit | Format   |
|-----------------|-----------------------------------------------------|------|----------|
| Employee Turnover % | Leavers during period / average headcount       | %    | 1 decimal|
| Absenteeism %   | Absence hours / scheduled work hours                | %    | 1 decimal|

---

## 5. Required Attributes (Business-Level)
- Employee, org, function, tenure band
- Status (active, leaver)
- Entry and exit dates
- Absence and work hours per period

---

## 6. Segmentation & Hierarchies
- Org: Region > Country > BusinessUnit  
- Function: Function > Department  
- Employee: Seniority > TenureBand  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Turnover is measured as voluntary and/or involuntary leavers, definition must be agreed.
- Headcount base is average over the period.

---

## 8. Data Freshness & Cadence
- HR data: monthly.
- Reporting cadence: monthly and quarterly HR reviews.

---

## 9. Edge Cases & QA Rules
- Employees without entry or exit dates are flagged.
- Absence and work hours must be non-negative and reconcile with payroll.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Headcount movement fact with status changes and hours.
  - Employee, org, and function dimensions.

---

## 11. Typical Actions
| Action                               | Code | Expected Effect          |
|--------------------------------------|------|--------------------------|
| Target retention initiatives at hotspots | C1 | Lower turnover          |
| Improve leadership or conditions in high-turnover units | SP1 | Better retention & engagement |
| Adjust recruiting focus and onboarding in critical roles | O2 | More stable workforce  |

---

## 12. Expected Business Impact
| Dimension | Expected Impact        | Measurement  |
|-----------|------------------------|--------------|
| People    | -1–2 pp turnover      | vs baseline  |
| Efficiency| Lower replacement cost| qualitative  |

---

## 13. Related Processes
Workforce Planning → Recruiting → Onboarding → Performance & Development.

---

## 14. Insights & Learnings
Typical findings include specific functions or regions with structural turnover issues and tenure bands with higher risk.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-002 Workforce Productivity & Turnover Analysis](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[HR-002 Workforce Productivity](../HR-002_Workforce_Productivity/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

