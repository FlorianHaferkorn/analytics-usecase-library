---
id: "OPS-015"
title: "OEE Advanced & Root Causes"
domain: "Operational Efficiency"
owner: "Head of Manufacturing / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct"]
action_codes: ["M2", "L2", "O2"]
expected_impact: "Deep-dive OEE into availability, performance and quality losses by root cause to prioritize the most impactful improvement actions."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 3M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Downtime_Codes_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.availability.pct",
    "ops.performance.pct",
    "ops.quality.pct",
    "ops.downtime.hours",
    "ops.machine_downtime.pct",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.availability.pct: "Availability %"
  ops.performance.pct: "Performance %"
  ops.quality.pct: "Quality %"
  ops.downtime.hours: "Downtime Hours"
  ops.machine_downtime.pct: "Machine Downtime %"
data_requirements:
  facts:
    - name: fact_mes_oee
      grain: asset_day
      primary_key: [AssetID, Date]
      required_columns:
        - { name: AssetID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: "Availability %", type: decimal, role: attribute }
        - { name: "Performance %", type: decimal, role: attribute }
        - { name: "Quality %", type: decimal, role: attribute }
        - { name: "OEE %", type: decimal, role: attribute }
    - name: fact_mes_events
      grain: event
      primary_key: [EventID]
      required_columns:
        - { name: EventID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: StartTime, type: datetime, role: date_key }
        - { name: EndTime, type: datetime, role: helper }
        - { name: "Event Type", type: string, role: attribute }
        - { name: "Loss Category", type: string, role: attribute } # e.g. Availability, Performance, Quality
        - { name: "Loss Reason", type: string, role: attribute }
        - { name: "Downtime Hours", type: decimal, role: amount }
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
        - { name: "Line", type: string }
  relationships:
    - { from: fact_mes_oee.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_mes_events.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "OEE %": "fact_mes_oee[OEE %]"
  "Availability %": "fact_mes_oee[Availability %]"
  "Performance %": "fact_mes_oee[Performance %]"
  "Quality %": "fact_mes_oee[Quality %]"
  "Downtime Hours": "fact_mes_events[Downtime Hours]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# OEE Advanced & Root Causes

## 1. Business Goal
Break down OEE into detailed loss categories and root causes so that maintenance and operations can focus on the most impactful improvements.

---

## 2. Business Context
OEE ist ein etablierter KPI in der Produktion, wird aber häufig nur als aggregierte Zahl betrachtet, ohne klare Ableitung konkreter Maßnahmen.  
Plant Manager und CI-Teams benötigen eine detaillierte Sicht auf Verfügbarkeits-, Leistungs- und Qualitätsverluste, um Investitionen und Verbesserungsprojekte zu priorisieren.  
Dieser Use Case verknüpft OEE mit Event- und Störungsdaten und stellt eine strukturierte Loss-Tree-Analyse bereit.

---

## 3. Key Questions
- Welche Anlagen und Linien weisen die schlechteste OEE auf, und welche Loss-Kategorien dominieren (Availability, Performance, Quality)?
- Welche konkreten Loss Reasons (z.B. Rüstzeiten, Störungen, Materialmangel) verursachen den größten Anteil an Downtime?
- Welche Verbesserungsmaßnahmen (z.B. SMED, TPM, Training) priorisieren wir zuerst je Linie/Asset?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability % * Performance % * Quality % | % |
| Availability % | (Planned Time - Downtime) / Planned Time | % |
| Performance % | Actual Output / Theoretical Output | % |
| Quality % | Good Units / Total Produced Units | % |
| Downtime Hours | Sum of downtime per asset/period | hours |

---

## 5. Required Attributes (Business-Level)
- Asset: ID, Family, Line, Standort.
- Time: Day, Week, Month.
- Loss Classification: Loss Category (Availability/Performance/Quality), Loss Reason.

---

## 6. Segmentation & Hierarchies
- Asset: Family > Line > Asset.
- Org: Region > Site.
- Time: Year > Month > Week > Day.

---

## 7. Scope & Assumptions
- OEE-Basisdefinition ist an bestehende OEE-Use Cases angepasst (OPS‑001/005).
- Loss-Reasons werden sukzessive standardisiert; initial können lokale Codes verwendet werden.
- Nicht alle Anlagen müssen gleichzeitig abgedeckt sein; Start mit kritischen Linien.

---

## 8. Data Freshness & Cadence
- MES-Eventdaten: nahe Echtzeit oder mindestens täglich.
- Reporting: täglich/wöchentlich für Shopfloor-Meetings; monatlich für Management-Reviews.

---

## 9. Edge Cases & QA Rules
- Fehleingaben oder fehlende Klassifikationen in Eventdaten müssen regelmäßig bereinigt werden.
- Änderungen in Asset-IDs oder Linienzuordnung sollten versioniert werden, um Zeitreihen zu sichern.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - OEE-Komponenten (Availability, Performance, Quality) pro Asset/Tag.
  - Event-/Störungsdaten mit Dauer und Lost Reason.
- Optional:
  - Produktionsmenge, Scrap-/Nacharbeitsdaten für zusätzliche Qualitätsanalysen.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Focus maintenance and CI projects on dominant loss categories | M2 | Schnellerer OEE-Anstieg durch zielgerichtete Maßnahmen |
| Implement SMED/TPM on high-setup or high-failure assets | L2 | Weniger Downtime und höhere Verfügbarkeit |
| Adjust production planning to reduce changeovers and micro-stops | O2 | Stabilere Performance und weniger Störungen |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Productivity | Höhere OEE und Ausbringung | OEE %, Output/Hour |
| Cost | Geringere Wartungs- und Störungskosten | Downtime Hours, Maintenance Cost |
| CAPEX Utilization | Bessere Auslastung bestehender Assets, reduzierte CAPEX-Bedarf | OEE vs. Design Capacity |

---

## 13. Related Processes
OEE Reporting -> Daily Shopfloor Meetings -> CI/Lean Projects -> Maintenance Planning -> Review & Sustain.

---

## 14. Insights & Learnings
Typisch ist, dass wenige Loss Reasons in bestimmten Anlagenfamilien den Großteil der Verluste ausmachen und dass vermeintlich „kleine“ Anpassungen (z.B. Rüstoptimierung) große Effekte auf OEE haben.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-001 Cash Conversion Cycle](../OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
  `[OPS-005 Capacity Utilization](../OPS-005_Capacity_Utilization/FactSheet.md)`  
  `[OPS-008 Unit Cost & COGS Drivers](../OPS-008_Unit_Cost_and_COGS_Drivers/FactSheet.md)`  
  `[OPS-013 Predictive Maintenance & Auto-Dispatch](../OPS-013_Predictive_Maintenance_and_Auto_Dispatch/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Manufacturing / Plant Manager] |
| Technical Reviewer | [MES / OEE Analyst] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first OEE improvement cycles] |

---

_Last updated: 19.11.2025_

