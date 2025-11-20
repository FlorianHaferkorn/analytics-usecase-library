---
id: "OPS-013"
title: "Predictive Maintenance & Auto-Dispatch"
domain: "Operational Efficiency"
owner: "Head of Maintenance / Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["OEE %", "Productivity %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct", "fin.liquidity.working_capital"]
action_codes: ["M2", "L2", "O2"]
expected_impact: "Reduce unplanned downtime and maintenance cost by predicting failures and automatically scheduling technicians and spare parts."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 6M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Failure_Codes_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.availability.pct",
    "ops.downtime.hours",
    "ops.machine_downtime.pct",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.availability.pct: "Availability %"
  ops.downtime.hours: "Downtime Hours"
  ops.machine_downtime.pct: "Machine Downtime %"
data_requirements:
  facts:
    - name: fact_mes_events
      grain: event
      primary_key: [EventID]
      required_columns:
        - { name: EventID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: StartTime, type: datetime, role: date_key }
        - { name: EndTime, type: datetime, role: helper }
        - { name: "Event Type", type: string, role: attribute }
        - { name: "Failure Code", type: string, role: attribute }
    - name: fact_maintenance_orders
      grain: maintenance_order
      primary_key: [OrderID]
      required_columns:
        - { name: OrderID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Order Type", type: string, role: attribute }
        - { name: "TechnicianID", type: string, role: attribute }
        - { name: "Planned Start", type: datetime, role: date_key }
        - { name: "Actual Start", type: datetime, role: helper }
        - { name: "Actual End", type: datetime, role: helper }
        - { name: "Maintenance Cost Amount", type: decimal, role: amount }
    - name: fact_production
      grain: production_run
      primary_key: [RunID]
      required_columns:
        - { name: RunID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Planned Qty", type: decimal, role: quantity }
        - { name: "Produced Qty", type: decimal, role: quantity }
        - { name: "Good Qty", type: decimal, role: quantity }
        - { name: "Run Start", type: datetime, role: date_key }
        - { name: "Run End", type: datetime, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Site, type: string }
    - name: dim_asset
      grain: asset
      primary_key: [AssetID]
      required_columns:
        - { name: "Asset Family", type: string }
        - { name: "Criticality", type: string }
  relationships:
    - { from: fact_mes_events.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_maintenance_orders.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_production.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "Downtime Hours": "fact_mes_events[Downtime Hours]"
  "Maintenance Cost Amount": "fact_maintenance_orders[Maintenance Cost Amount]"
  "Planned Qty": "fact_production[Planned Qty]"
  "Produced Qty": "fact_production[Produced Qty]"
  "Good Qty": "fact_production[Good Qty]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# Predictive Maintenance & Auto-Dispatch

## 1. Business Goal
Reduce unplanned downtime and maintenance cost by predicting failures, planning maintenance proactively and automatically dispatching technicians and spare parts where needed most.

---

## 2. Business Context
Maintenance is often reactive: assets are run to failure, leading to ungeplante Stillstände, Express-Beschaffung von Ersatzteilen und ineffiziente Techniker-Einsätze.  
Zwar gibt es häufig Wartungspläne, diese sind jedoch statisch (z.B. nach Zeitintervallen) und berücksichtigen nicht reale Belastung und Zustände.  
Predictive Maintenance & Auto-Dispatch nutzt Maschinendaten, Ereignislogs und Wartungshistorie, um Ausfälle vorherzusagen und Einsätze vorausschauend zu planen.

---

## 3. Key Questions
- Welche Assets weisen aktuell ein erhöhtes Ausfallrisiko auf – und in welchem Zeithorizont?
- Wo können wir geplanter statt ungeplanter Wartung durchführen, ohne OEE unnötig zu beeinträchtigen?
- Wie verteilen wir Techniker und Ersatzteile optimal auf Standorte und Assets?
- Wie verändern sich OEE, Availability und Downtime Hours nach Einführung von Predictive Maintenance?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability * Performance * Quality | % |
| Availability % | (Planned Time - Downtime) / Planned Time | % |
| Downtime Hours | Sum of unplanned and planned downtime | hours |
| Machine Downtime % | Downtime / Planned Time | % |

---

## 5. Required Attributes (Business-Level)
- Asset: ID, Family, Criticality, Standort.
- Time: Day, Week, Month.
- Maintenance: Order Type (planned/unplanned), Technician, Duration, Cost.
- Events: Event Type, Failure Code, Start/End.

---

## 6. Segmentation & Hierarchies
- Asset: Family > Asset > Subsystem (optional).
- Org: Region > Site.
- Time: Year > Month > Week > Day.

---

## 7. Scope & Assumptions
- Predictive-Model-Details (Feature Engineering, Algorithmus) liegen außerhalb dieses FactSheets; hier werden primär KPIs und Datenanforderungen beschrieben.
- Auto-Dispatch erzeugt Vorschläge (z.B. „Assign Technician X at Slot Y“); Umsetzung kann über externe Systeme (CMMS, FSM) erfolgen.
- Nicht alle Assets müssen initial abgedeckt werden; Start mit kritischen Anlagen/Familien.

---

## 8. Data Freshness & Cadence
- MES-Eventdaten: nahe Echtzeit oder mindestens täglich.
- Maintenance Orders: bei Auftragserfassung/-abschluss aktualisiert.
- KPI-Reporting: täglich/wöchentlich, mit Monatsabschluss-Sicht.

---

## 9. Edge Cases & QA Rules
- Assets mit unvollständiger Sensorik oder unzuverlässigen Daten werden separat behandelt.
- Manuelle Eingriffe (z.B. Wartungen ohne Order) sollten im System abgebildet oder dokumentiert werden.
- Modellfehlalarme (false positives) werden überwacht, um nicht unnötig Wartung auszulösen.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Eventlogs (Downtime, Failure Codes) je Asset.
  - Maintenance-Orders mit Typ, Dauer, Kosten.
  - Produktionsdaten (Planned/Produced/Good Qty) zur Berechnung von OEE-Komponenten.
- Optional:
  - Sensor-/Condition-Monitoring-Daten für fortgeschrittene Modelle.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Plan maintenance windows based on predicted failures | M2 | Reduzierte ungeplante Stillstände, stabilere OEE |
| Auto-dispatch technicians and parts to high-risk assets | L2 | Bessere Ressourcenauslastung, kürzere MTTR |
| Adjust maintenance strategy based on asset criticality and failure patterns | O2 | Geringere Gesamtwartungskosten bei gleichbleibender Verfügbarkeit |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Availability | Weniger ungeplante Downtime | Downtime Hours, Machine Downtime % |
| Efficiency | Besser ausgelastete Techniker, weniger Express-Beschaffungen | Wartungskosten, Techniker-Produktivität |
| Capacity | Höhere Produktionsverfügbarkeit und Durchsatz | OEE %, Performance % |

---

## 13. Related Processes
Asset Master Data Management -> Condition Monitoring -> Predictive Model Scoring -> Maintenance Planning -> Execution & Feedback.

---

## 14. Insights & Learnings
Typische Insights sind wiederkehrende Fehlerbilder bei bestimmten Asset-Familien, saisonale oder lastabhängige Ausfallmuster und ineffiziente Einsatzplanung (z.B. häufige Fahrten zu entfernten Sites für kleine Reparaturen).

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-005 Capacity Utilization](../OPS-005_Capacity_Utilization/FactSheet.md)`  
  `[OPS-008 Unit Cost & COGS Drivers](../OPS-008_Unit_Cost_and_COGS_Drivers/FactSheet.md)`  
  `[COR-011 Integrated S&OP](../../04_Corporate_and_Strategy/COR-011_Integrated_S&OP/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Maintenance / Operations] |
| Technical Reviewer | [Maintenance Engineer / Data Scientist] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after pilot] |

---

_Last updated: 19.11.2025_

