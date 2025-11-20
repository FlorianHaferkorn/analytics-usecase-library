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

# Use Case Fact Sheet

## 1. Business Goal
Systematische Ãœberwachung der DatenqualitÃ¤t Ã¼ber DomÃ¤nen hinweg, um Risiken fÃ¼r Berichte und Analytics frÃ¼hzeitig zu erkennen.

## 2. Business Questions
- Welche Tabellen haben die niedrigste Data Quality %?
- Welche Domains verursachen die meisten DQ-Issues?

## 3. Scope & Assumptions
- Fokus auf kritische Berichts- und Analytics-Tabellen laut Data Catalog.

## 4. Target Users & Decisions
- Zielgruppe: Data Governance, Domain Owner, BI Teams.
- Entscheidungen: Priorisierung von DQ-MaÃŸnahmen, Verantwortlichkeiten klÃ¤ren.

## 5. KPIs & Drivers (Overview)
- Data Quality %, Valid vs. Total Records, DQ-Issue-Trends.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- DQ-Regeln und Checks mÃ¼ssen versioniert und dokumentiert sein.

## 8. Page Layout / Storyboard
- Overview: DQ-Scores nach Domain/Subject Area.
- Drivers: Regel-Ebene, Zeitverlauf, Root-Cause-Analyse.
