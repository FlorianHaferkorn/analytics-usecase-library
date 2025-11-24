---
id: "COR-002"
title: "Workforce Productivity & Turnover Analysis"
domain: "Corporate and Strategy"
owner: "Head of HR Controlling / People Analytics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue per FTE", "Personnel Cost Ratio %", "Turnover Rate %"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "hr.personnel_cost_ratio.pct", "hr.turnover.pct"]
action_codes: ["C1", "SP1", "O2", "D1", "O3"]
expected_impact: "+5-10 % Revenue per FTE; -2-4 % Personnel Cost Ratio; +3-5 pp turnover improvement"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Department",
  "Workforce.Function>Team",
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
  "hr.revenue_per_fte.amount",
  "hr.gm_per_fte.amount",
  "hr.personnel_cost_ratio.pct",
  "hr.turnover.pct",
  "hr.absenteeism.pct"
]
required_kpis:
  hr.revenue_per_fte.amount: "Revenue per FTE"
  hr.gm_per_fte.amount: "Gross Margin per FTE"
  hr.personnel_cost_ratio.pct: "Personnel Cost Ratio %"
  hr.turnover.pct: "Turnover Rate %"
  hr.absenteeism.pct: "Absenteeism %"
data_requirements:
  facts:
    - name: fact_hr_headcount
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: EmployeeID, type: string, role: employee_key }
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: Department, type: string, role: attribute }
        - { name: Function, type: string, role: attribute }
        - { name: Country, type: string, role: attribute }
        - { name: FTEFactor, type: decimal, role: helper }
        - { name: ContractType, type: string, role: attribute }
        - { name: HireDate, type: date, role: helper }
        - { name: LeaveDate, type: date, role: helper }
    - name: fact_hr_cost
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: PersonnelCost, type: decimal, role: amount }
        - { name: BonusCost, type: decimal, role: amount }
        - { name: OvertimeCost, type: decimal, role: amount }
    - name: fact_financials
      grain: org_month
      primary_key: [OrgID, SnapshotMonth]
      required_columns:
        - { name: RevenueAmount, type: decimal, role: amount }
        - { name: GrossMarginAmount, type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_hr_headcount.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_hr_headcount.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_hr_cost.EmployeeID, to: fact_hr_headcount.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_financials.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_financials.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Employee": "fact_hr_headcount[EmployeeID]"
  "Region": "dim_org[Region]"
  "Department": "fact_hr_headcount[Department]"
  "FTE": "fact_hr_headcount[FTEFactor]"
  "Personnel Cost": "fact_hr_cost[PersonnelCost]"
  "Revenue Amount": "fact_financials[RevenueAmount]"
  "Gross Margin Amount": "fact_financials[GrossMarginAmount]"
  "Snapshot Month": "fact_hr_headcount[SnapshotMonth]"
---

# Workforce Productivity & Turnover Analysis

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
