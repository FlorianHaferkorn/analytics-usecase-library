---
id: "OPS-016"
title: "Bottleneck & Throughput Analysis (TOC)"
domain: "Operational Efficiency"
owner: "Head of Operations / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct"]
action_codes: ["M2", "L2", "SP1"]
expected_impact: "Identify and manage production bottlenecks to increase overall throughput without immediate CAPEX investments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 3M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Routing_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.performance.pct",
    "ops.produced_units.qty",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.performance.pct: "Performance %"
  ops.produced_units.qty: "Produced Units Qty"
data_requirements:
  facts:
    - name: fact_production
      grain: production_run
      primary_key: [RunID]
      required_columns:
        - { name: RunID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Good Units Qty", type: decimal, role: quantity }
        - { name: "Run Start", type: datetime, role: date_key }
        - { name: "Run End", type: datetime, role: helper }
    - name: fact_mes_oee
      grain: asset_day
      primary_key: [AssetID, Date]
      required_columns:
        - { name: AssetID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: "OEE %", type: decimal, role: attribute }
        - { name: "Performance %", type: decimal, role: attribute }
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
    - { from: fact_production.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_mes_oee.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Good Units Qty": "fact_production[Good Units Qty]"
  "OEE %": "fact_mes_oee[OEE %]"
  "Performance %": "fact_mes_oee[Performance %]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# Bottleneck & Throughput Analysis (TOC)

## 1. Business Goal
Increase overall production throughput and shorten lead times by identifying and managing bottleneck resources according to the Theory of Constraints.

---

## 2. Business Context
In vielen Fertigungsumgebungen bestimmt ein kleiner Teil der Anlagen oder Linien den Gesamtdurchsatz – unabhängig davon, wie stark andere Ressourcen optimiert werden.  
Ohne klare, datenbasierte Identifikation und Steuerung des Engpasses laufen Verbesserungsinitiativen ins Leere oder werden durch nachgelagerte Engpässe kompensiert.  
Dieser Use Case kombiniert OEE-/Performance-Kennzahlen mit Durchsatzdaten, um Engpässe sichtbar zu machen und Maßnahmen entlang der TOC-Logik abzuleiten.

---

## 3. Key Questions
- Welche Anlage oder Linie ist der aktuelle Engpass im betrachteten Wertstrom?
- Wie stabil ist dieser Engpass über Zeit – oder wandert er zwischen Ressourcen?
- Welche Maßnahmen (z.B. Schichtanpassung, Setup-Reduktion, Priorisierung) erhöhen den Durchsatz am Engpass am stärksten?
- Wie wirken sich Engpassmaßnahmen auf Gesamt-Output, OEE und Lieferzeiten aus?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability * Performance * Quality | % |
| Performance % | Actual Output / Theoretical Output | % |
| Produced Units Qty | Total units produced per asset/period | units |
| Good Units Qty | Good units produced (excl. scrap) per asset/period | units |

---

## 5. Required Attributes (Business-Level)
- Asset: ID, Family, Line, Standort.
- Time: Day, Week, Month.
- Production: Planned vs actual quantities per run.

---

## 6. Segmentation & Hierarchies
- Asset: Line > Asset.
- Org: Region > Site.
- Time: Year > Month > Week > Day.

---

## 7. Scope & Assumptions
- Wertstrom-Definition (Sequenz der Anlagen) ist bekannt; Engpassanalyse erfolgt pro Wertstrom.
- CAPEX-Beschränkungen bedeuten, dass vorrangig Prozess- und Planungsmaßnahmen statt neuer Anlagen betrachtet werden.

---

## 8. Data Freshness & Cadence
- Produktionsdaten: täglich/Schicht-basiert.
- Reporting: täglich/wöchentlich für Shopfloor- und S&OP-Reviews.

---

## 9. Edge Cases & QA Rules
- Datenlücken bei Produktionsmengen oder OEE können Engpassanalyse verfälschen; Qualitätschecks sind nötig.
- Engpass kann sich bei größeren Veränderungen (z.B. Produktmix, Nachfrage, CAPEX) verschieben und sollte regelmäßig neu bestimmt werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Produktivitätsdaten (OEE/Performance) pro Asset/Periode.
  - Produktionsmengen (Produced/Good Qty) pro Asset/Periode.
- Optional:
  - Setup-Zeiten, Queue-/Wartezeiten pro Auftragssegment.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Elevate capacity at bottleneck resources (shifts, staffing) | M2 | Higher throughput, reduced backlog |
| Reduce setup and changeover on bottleneck lines | L2 | Mehr effektive Produktionszeit, weniger Micro-Stops |
| Re-sequence production to prioritize bottleneck utilization | SP1 | Kürzere Durchlaufzeiten und stabilere Auslastung |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Throughput | Höherer Output ohne sofortige CAPEX-Erhöhung | Produced/Good Qty per period |
| Lead Time | Kürzere Durchlaufzeiten im Wertstrom | Lead Time (Prozesssicht) |
| Cost | Bessere Fixkostendegression, geringere Stückkosten | Unit Cost, OEE |

---

## 13. Related Processes
Capacity Planning -> Production Scheduling -> Daily Shopfloor Management -> Continuous Improvement / TOC Projects.

---

## 14. Insights & Learnings
Typischerweise zeigt sich, dass vermeintliche Engpässe nicht die wahren limitierenden Faktoren sind und dass gezielte Maßnahmen an wenigen Ressourcen starke Wirkung auf Gesamtperformance haben.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-005 Capacity Utilization](../OPS-005_Capacity_Utilization/FactSheet.md)`  
  `[OPS-008 Unit Cost & COGS Drivers](../OPS-008_Unit_Cost_and_COGS_Drivers/FactSheet.md)`  
  `[OPS-013 Predictive Maintenance & Auto-Dispatch](../OPS-013_Predictive_Maintenance_and_Auto_Dispatch/FactSheet.md)`  
  `[COR-011 Integrated S&OP](../../04_Corporate_and_Strategy/COR-011_Integrated_S&OP/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
--------|--------|
| Business Reviewer | [Head of Operations / Plant Manager] |
| Technical Reviewer | [Production Planning / OEE Analyst] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first TOC projects] |

---

_Last updated: 19.11.2025_

