---
id: "GOV-001"
title: "Data Quality Monitoring"
domain: "Governance"
owner: "Chief Data Officer / Data Governance Lead"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Data Quality %", "Governance Score"]
supports_strategic_kpi_ids: ["gov.data_quality.pct"]
action_codes: ["G1", "G2"]
expected_impact: "+2 pp Data Quality %, -20 % Issues durch kontinuierliches Monitoring."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Domain>SubjectArea>Table",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 3M",
  "Domain: All"
]
qa_asserts: ["RI_OK", "DQ_Score_Within_Range"]
required_kpi_ids: [
  "gov.data_quality.pct",
  "gov.valid_records.count",
  "gov.records.total.count"
]
required_kpis:
  gov.data_quality.pct: "Data Quality %"
  gov.valid_records.count: "Valid Records Count"
  gov.records.total.count: "Total Records Count"
data_requirements:
  facts:
    - name: fact_dq_checks
      grain: table_day
      primary_key: [Domain, SubjectArea, TableName, CheckDate]
      required_columns:
        - { name: Domain, type: string, role: attribute }
        - { name: SubjectArea, type: string, role: attribute }
        - { name: TableName, type: string, role: attribute }
        - { name: CheckDate, type: date, role: date_key }
        - { name: ValidRecords, type: int, role: amount }
        - { name: TotalRecords, type: int, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_dq_checks.CheckDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Valid Records": "fact_dq_checks[ValidRecords]"
  "Total Records": "fact_dq_checks[TotalRecords]"
---

# Data Quality Monitoring

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
