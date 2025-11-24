---
id: "GOV-004"
title: "Audit Findings Management"
domain: "Governance"
owner: "Head of Internal Audit / Action Owner"
impact: "Medium"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Governance Score %", "Data Quality %"]
supports_strategic_kpi_ids: ["gov.audit.findings.open.count"]
action_codes: ["G2", "G5"]
expected_impact: "-15 % Open Findings, schnellere Umsetzung von MaÃŸnahmen."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "Finding.Severity>Status",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Severity: All",
  "Status: All"
]
qa_asserts: ["RI_OK", "Aging_Captured", "Owner_Assigned"]
required_kpi_ids: [
  "gov.audit.findings.open.count",
  "gov.audit.findings.count"
]
required_kpis:
  gov.audit.findings.open.count: "Open Audit Findings Count"
  gov.audit.findings.count: "Total Audit Findings Count"
data_requirements:
  facts:
    - name: fact_findings
      grain: finding
      primary_key: [FindingID]
      required_columns:
        - { name: FindingID, type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
        - { name: Severity, type: string, role: attribute }
        - { name: Status, type: string, role: attribute }
        - { name: OpenDate, type: date, role: date_key }
        - { name: CloseDate, type: date, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
model_mapping:
  "Finding ID": "fact_findings[FindingID]"
  "Finding Severity": "fact_findings[Severity]"
  "Finding Status": "fact_findings[Status]"
  "Finding Open Date": "fact_findings[OpenDate]"
---

# Audit Findings Management

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
