---
id: "GOV-002"
title: "Access & Compliance Review"
domain: "Governance"
owner: "CISO / Compliance Officer"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Governance Score", "Audit Findings %"]
supports_strategic_kpi_ids: ["gov.compliance.incidents.count"]
action_codes: ["G3", "G4"]
expected_impact: "-10 % Violations durch strukturierte Zugriffs- und Compliance-Reviews."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "System>App>Role",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "System: All"
]
qa_asserts: ["RI_OK", "Violations_Tracked"]
required_kpi_ids: [
  "gov.compliance.incidents.count",
  "gov.compliance.breach.count"
]
required_kpis:
  gov.compliance.incidents.count: "Compliance Incidents Count"
  gov.compliance.breach.count: "Compliance Breach Count"
data_requirements:
  facts:
    - name: fact_compliance
      grain: incident
      primary_key: [IncidentID]
      required_columns:
        - { name: IncidentID, type: string, role: attribute }
        - { name: System, type: string, role: attribute }
        - { name: Severity, type: string, role: attribute }
        - { name: IsBreach, type: bool, role: indicator }
        - { name: OpenDate, type: date, role: date_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
model_mapping:
  "Compliance Incidents Count": "fact_compliance[IncidentID]"
  "Compliance Breach Flag": "fact_compliance[IsBreach]"
  "Incident Open Date": "fact_compliance[OpenDate]"
---

# Use Case Fact Sheet

## 1. Business Goal
Sicherstellen, dass Benutzerzugriffe und Compliance-Anforderungen eingehalten werden und VerstÃ¶ÃŸe transparent Ã¼berwacht werden.

## 2. Business Questions
- Wie viele Compliance-Incidents und -Breaches treten pro System/Org auf?
- Wie entwickeln sich diese Kennzahlen Ã¼ber die Zeit?

## 3. Scope & Assumptions
- Fokus auf kritische Systeme (ERP, CRM, BI).

## 4. Target Users & Decisions
- Zielgruppe: CISO, Compliance, Internal Audit.
- Entscheidungen: Zugriffsbereinigung, zusÃ¤tzliche Kontrollen, SchulungsmaÃŸnahmen.

## 5. KPIs & Drivers (Overview)
- Compliance Incidents Count, Breach Count, Trends nach System/Severity.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- Incidents mÃ¼ssen eindeutig klassifiziert sein (Severity, Root Cause).

## 8. Page Layout / Storyboard
- Overview: Incident-Heatmap nach System/Org.
- Drivers: Severity, Root Cause, Zeitverlauf.
