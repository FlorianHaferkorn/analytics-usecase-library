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
expected_impact: "+0.5 pp Productivity, +3 pp Engagement durch gezielte TrainingsmaÃŸnahmen."
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

# Employee Development & Learning

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
