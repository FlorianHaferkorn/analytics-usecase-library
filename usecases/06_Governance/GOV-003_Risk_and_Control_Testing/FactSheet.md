---
id: "GOV-003"
title: "Risk & Control Testing"
domain: "Governance"
owner: "Head of Internal Audit / Risk Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Governance Score %", "Audit Finding Severity %"]
supports_strategic_kpi_ids: ["gov.audit.findings.count", "gov.audit.findings.open.count"]
action_codes: ["G5"]
expected_impact: "+5 pp Control Pass Rate, -15 % Findings Severity."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Risk.Category>Process>Control",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter"
]
filters_default: [
  "Time: Last 12M",
  "Risk Category: All"
]
qa_asserts: ["RI_OK", "Controls_Tested", "Findings_Tracked"]
required_kpi_ids: [
  "gov.audit.findings.count",
  "gov.audit.findings.open.count"
]
required_kpis:
  gov.audit.findings.count: "Audit Findings Count"
  gov.audit.findings.open.count: "Open Audit Findings Count"
data_requirements:
  facts:
    - name: fact_controls
      grain: control_test
      primary_key: [ControlTestID]
      required_columns:
        - { name: ControlID, type: string, role: attribute }
        - { name: TestDate, type: date, role: date_key }
        - { name: Result, type: string, role: attribute }
    - name: fact_findings
      grain: finding
      primary_key: [FindingID]
      required_columns:
        - { name: FindingID, type: string, role: attribute }
        - { name: ControlID, type: string, role: attribute }
        - { name: Severity, type: string, role: attribute }
        - { name: IsOpen, type: bool, role: indicator }
        - { name: OpenDate, type: date, role: date_key }
  dims:
    - name: dim_control
      grain: control
      primary_key: [ControlID]
      required_columns:
        - { name: RiskCategory, type: string }
        - { name: Process, type: string }
        - { name: ControlName, type: string }
model_mapping:
  "Control Test Result": "fact_controls[Result]"
  "Control": "dim_control[ControlID]"
  "Finding Severity": "fact_findings[Severity]"
---

# Use Case Fact Sheet

## 1. Business Goal
Wirksamkeit des internen Kontrollsystems monitoren, indem Testergebnisse und Findings konsolidiert werden.

## 2. Business Questions
- Wie viele Kontrollen bestehen/nicht bestehen pro Risiko- und Prozesskategorie?
- Wie viele Findings sind offen und mit welcher Severity?

## 3. Scope & Assumptions
- Fokus auf SOX-/kritische Kontrollen und interne Revision.

## 4. Target Users & Decisions
- Zielgruppe: Risk Management, Internal Audit, Process Owner.
- Entscheidungen: Priorisierung von Remediation-MaÃŸnahmen, Anpassung von Kontrollen.

## 5. KPIs & Drivers (Overview)
- Audit Findings Count, Open Findings Count, Control Pass Rate.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- Control- und Finding-IDs mÃ¼ssen stabil und eindeutig sein.

## 8. Page Layout / Storyboard
- Overview: Control Pass/Fail und Findings nach Kategorie.
- Drivers: Severity, Aging, Verantwortliche.
