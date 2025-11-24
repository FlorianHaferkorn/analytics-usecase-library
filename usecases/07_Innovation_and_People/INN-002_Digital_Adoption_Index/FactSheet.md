---
id: "INN-002"
title: "Digital Adoption Index"
domain: "Innovation & People"
owner: "Head of Digital Transformation / CIO"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Digital Adoption Rate %", "Automation Rate %"]
supports_strategic_kpi_ids: ["people.digital_adoption.pct"]
action_codes: ["I3"]
expected_impact: "+5 pp Adoption durch gezieltes Change- und Enablement-Management."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit>Department",
  "Process.Area>Subprocess",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Process Area: All"
]
qa_asserts: ["RI_OK", "UsageEvents_Tracked"]
required_kpi_ids: [
  "people.digital_adoption.pct"
]
required_kpis:
  people.digital_adoption.pct: "Digital Adoption Rate %"
data_requirements:
  facts:
    - name: fact_digital_usage
      grain: process_user_day
      primary_key: [UserID, ProcessID, UsageDate]
      required_columns:
        - { name: UserID, type: string, role: attribute }
        - { name: ProcessID, type: string, role: attribute }
        - { name: UsageDate, type: date, role: date_key }
        - { name: IsDigital, type: bool, role: indicator }
        - { name: TransactionsCount, type: int, role: amount }
    - name: fact_process_baseline
      grain: process
      primary_key: [ProcessID]
      required_columns:
        - { name: IsEligibleForDigital, type: bool, role: indicator }
  dims:
    - name: dim_process
      grain: process
      primary_key: [ProcessID]
      required_columns:
        - { name: ProcessArea, type: string }
        - { name: Subprocess, type: string }
model_mapping:
  "Process": "dim_process[ProcessID]"
  "Transactions Count": "fact_digital_usage[TransactionsCount]"
  "Is Digital Flag": "fact_digital_usage[IsDigital]"
---

# Digital Adoption Index

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
