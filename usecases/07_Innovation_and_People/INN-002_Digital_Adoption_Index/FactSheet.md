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

# Use Case Fact Sheet

## 1. Business Goal
Grad der Nutzung digitaler Prozesse und Tools sichtbar machen, um manuelle Arbeit zu reduzieren und Automatisierung voranzutreiben.

## 2. Business Questions
- Wie hoch ist der Digital Adoption Rate % pro Prozess/Org?
- Welche Prozesse werden noch Ã¼berwiegend manuell ausgefÃ¼hrt?

## 3. Scope & Assumptions
- Nur Prozesse mit definiertem digitalen Zielbild und Usage-Tracking werden berÃ¼cksichtigt.

## 4. Target Users & Decisions
- Zielgruppe: Digital Transformation, IT, Process Owner.
- Entscheidungen: Priorisierung von Digitalisierungsinitiativen, Change & Training.

## 5. KPIs & Drivers (Overview)
- Digital Adoption Rate %, Automatisierungsgrad, manuelle vs. digitale Transaktionen.

## 6. Required KPIs (Detail)
Noch nicht im KPI-Katalog hinterlegt; wird in einem spÃ¤teren Schritt ergÃ¤nzt.

## 7. Data & Modelling Notes
- Konsistentes Usage-Tracking und Zuordnung zu Prozessen ist kritisch.

## 8. Page Layout / Storyboard
- Overview: Digital Adoption nach Org/Process Area.
- Drivers: Manuelle Restarbeit, Zeitverlauf, Nutzergruppen.
