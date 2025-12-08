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

# OEE Advanced & Root Causes - Business Factsheet

## 1. Summary
- **Business Goal:** Break down OEE into detailed loss categories and root causes so that maintenance and operations can focus on the most impactful improvements.
- **Target Audience:** Head of Manufacturing / Plant Manager
- **Business Priority:** High
- **Expected Impact:** Deep-dive OEE into availability, performance and quality losses by root cause to prioritize the most impactful improvement actions.

## 2. Core Questions
- Welche Anlagen und Linien weisen die schlechteste OEE auf, und welche Loss-Kategorien dominieren (Availability, Performance, Quality)?
- Welche konkreten Loss Reasons (z.B. Rstzeiten, Strungen, Materialmangel) verursachen den grten Anteil an Downtime?
- Welche Verbesserungsmanahmen (z.B. SMED, TPM, Training) priorisieren wir zuerst je Linie/Asset?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability % * Performance % * Quality % | % |
| Availability % | (Planned Time - Downtime) / Planned Time | % |
| Performance % | Actual Output / Theoretical Output | % |
| Quality % | Good Units / Total Produced Units | % |
| Downtime Hours | Sum of downtime per asset/period | hours |

## 4. Business Logic & Thresholds
- Fehleingaben oder fehlende Klassifikationen in Eventdaten mssen regelmig bereinigt werden.
- nderungen in Asset-IDs oder Linienzuordnung sollten versioniert werden, um Zeitreihen zu sichern.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Focus maintenance and CI projects on dominant loss categories | M2 | Schnellerer OEE-Anstieg durch zielgerichtete Manahmen |
| Implement SMED/TPM on high-setup or high-failure assets | L2 | Weniger Downtime und hhere Verfgbarkeit |
| Adjust production planning to reduce changeovers and micro-stops | O2 | Stabilere Performance und weniger Strungen |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Overall Equipment Effectiveness (OEE) %, Availability %, Performance %, Quality %, Downtime Hours with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- OEE-Basisdefinition ist an bestehende OEE-Use Cases angepasst (OPS001/005).
- Loss-Reasons werden sukzessive standardisiert; initial knnen lokale Codes verwendet werden.
- Nicht alle Anlagen mssen gleichzeitig abgedeckt sein; Start mit kritischen Linien.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Productivity | Hhere OEE und Ausbringung | OEE %, Output/Hour |
| Cost | Geringere Wartungs- und Strungskosten | Downtime Hours, Maintenance Cost |
| CAPEX Utilization | Bessere Auslastung bestehender Assets, reduzierte CAPEX-Bedarf | OEE vs. Design Capacity |