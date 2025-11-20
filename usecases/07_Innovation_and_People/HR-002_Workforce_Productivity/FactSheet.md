---
id: "HR-002"
title: "Workforce Productivity"
domain: "Corporate and Strategy"
owner: "Head of HR / People Analytics"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Productivity per FTE", "Absenteeism %"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "hr.absenteeism.pct"]
action_codes: ["H3", "H4"]
expected_impact: "+1 pp Productivity, -0.5 pp Absenteeism durch bessere Einsatzplanung und GesundheitsmaÃŸnahmen."
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
qa_asserts: ["RI_OK", "Hours_Reconcile", "Headcount_Consistent"]
required_kpi_ids: [
  "hr.revenue_per_fte.amount",
  "hr.gm_per_fte.amount",
  "hr.personnel_cost_ratio.pct",
  "hr.absenteeism.pct"
]
required_kpis:
  hr.revenue_per_fte.amount: "Revenue per FTE"
  hr.gm_per_fte.amount: "Gross Margin per FTE"
  hr.personnel_cost_ratio.pct: "Personnel Cost Ratio %"
  hr.absenteeism.pct: "Absenteeism %"
data_requirements:
  facts:
    - name: fact_hr_headcount
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: EmployeeID, type: string, role: employee_key }
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: FTE, type: decimal, role: amount }
        - { name: ScheduledHours, type: decimal, role: amount }
        - { name: AbsentHours, type: decimal, role: amount }
        - { name: OrgID, type: string, role: org_key }
    - name: fact_financials
      grain: org_month
      primary_key: [OrgID, Month]
      required_columns:
        - { name: RevenueAmount, type: decimal, role: amount }
        - { name: GrossMarginAmount, type: decimal, role: amount }
        - { name: PersonnelCostAmount, type: decimal, role: amount }
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
    - { from: fact_hr_headcount.EmployeeID, to: dim_employee.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_hr_headcount.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
model_mapping:
  "FTE": "fact_hr_headcount[FTE]"
  "Scheduled Hours": "fact_hr_headcount[ScheduledHours]"
  "Absent Hours": "fact_hr_headcount[AbsentHours]"
  "Revenue Amount": "fact_financials[RevenueAmount]"
  "Gross Margin Amount": "fact_financials[GrossMarginAmount]"
  "Personnel Cost Amount": "fact_financials[PersonnelCostAmount]"
---

# Use Case Fact Sheet

## 1. Business Goal
Workforce-ProduktivitÃ¤t und Ausfallzeiten transparent machen, um gezielt Effizienz- und GesundheitsmaÃŸnahmen zu steuern.

## 2. Business Questions
- Wie entwickelt sich Revenue/Gross Margin per FTE Ã¼ber Organisation und Zeit?
- Wo sind Ausfallzeiten (Absenteeism) besonders hoch und wie beeinflussen sie die ProduktivitÃ¤t?

## 3. Scope & Assumptions
- Fokus auf interne Mitarbeiter (keine externen Ressourcen).
- FTE und Arbeitsstunden sind mit Finance/HR abgestimmt.

## 4. Target Users & Decisions
- Zielgruppe: HR, People Analytics, Linienmanager, Controlling.
- Entscheidungen: Besetzungsgrade, Priorisierung von Effizienz-Programmen, Gesundheits- und Engagement-Initiativen.

## 5. KPIs & Drivers (Overview)
- Revenue per FTE, Gross Margin per FTE, Personnel Cost Ratio %, Absenteeism %.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- Consistenter Join zwischen HR-Headcount und Financials auf Org/Periodenebene ist kritisch.

## 8. Page Layout / Storyboard
- Overview: ProduktivitÃ¤t und Absenteeism pro Org/Department.
- Drivers: Rollen/Level, Kostenstruktur, Zeitverlauf.
