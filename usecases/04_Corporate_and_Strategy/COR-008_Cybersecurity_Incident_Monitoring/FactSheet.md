---
id: "COR-008"
title: "Cybersecurity Incident Monitoring"
domain: "Corporate and Strategy"
owner: "CISO / Head of IT Security"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Cyber Incident Count", "Regulatory Reporting Timeliness %"]
supports_strategic_kpi_ids: ["sec.incident.count", "gov.compliance.breach.count"]
action_codes: ["G3", "G4", "SP1"]
expected_impact: "Fewer critical incidents; faster detection and response; better compliance posture."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "System>Application",
  "Incident.Severity>Category",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Severity: All",
  "System: All"
]
qa_asserts: ["RI_OK", "Incidents_Tracked", "Severity_Classification_Consistent"]
required_kpi_ids: [
  "sec.incident.count",
  "sec.incident.critical.count",
  "sec.incident.mttr.hours"
]
required_kpis:
  sec.incident.count: "Cybersecurity Incident Count"
  sec.incident.critical.count: "Critical Incidents Count"
  sec.incident.mttr.hours: "Mean Time to Resolve (MTTR) Hours"
data_requirements:
  facts:
    - name: fact_security_incidents
      grain: incident
      primary_key: [IncidentID]
      required_columns:
        - { name: IncidentID, type: string, role: attribute }
        - { name: "Detected Date", type: date, role: date_key }
        - { name: "Resolved Date", type: date, role: helper }
        - { name: "Severity", type: string, role: status }
        - { name: "Category", type: string, role: attribute }
        - { name: "Source System", type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
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
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_security_incidents.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_security_incidents."Detected Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Incident ID": "fact_security_incidents[IncidentID]"
  "Severity": "fact_security_incidents[Severity]"
  "Category": "fact_security_incidents[Category]"
  "Detected Date": "fact_security_incidents[Detected Date]"
  "Resolved Date": "fact_security_incidents[Resolved Date]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Cybersecurity Incident Monitoring

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
