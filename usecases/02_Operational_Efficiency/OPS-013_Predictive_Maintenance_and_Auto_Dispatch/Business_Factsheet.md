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

# Predictive Maintenance & Auto-Dispatch - Business Factsheet

## 1. Summary
- **Business Goal:** Reduce unplanned downtime and maintenance cost by predicting failures, planning maintenance proactively and automatically dispatching technicians and spare parts where needed most.
- **Target Audience:** Head of Maintenance / Operations
- **Business Priority:** High
- **Expected Impact:** Reduce unplanned downtime and maintenance cost by predicting failures and automatically scheduling technicians and spare parts.

## 2. Core Questions
- Welche Assets weisen aktuell ein erhhtes Ausfallrisiko auf - und in welchem Zeithorizont?
- Wo knnen wir geplanter statt ungeplanter Wartung durchfhren, ohne OEE unntig zu beeintrchtigen?
- Wie verteilen wir Techniker und Ersatzteile optimal auf Standorte und Assets?
- Wie verndern sich OEE, Availability und Downtime Hours nach Einfhrung von Predictive Maintenance?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability * Performance * Quality | % |
| Availability % | (Planned Time - Downtime) / Planned Time | % |
| Downtime Hours | Sum of unplanned and planned downtime | hours |
| Machine Downtime % | Downtime / Planned Time | % |

## 4. Business Logic & Thresholds
- Assets mit unvollstndiger Sensorik oder unzuverlssigen Daten werden separat behandelt.
- Manuelle Eingriffe (z.B. Wartungen ohne Order) sollten im System abgebildet oder dokumentiert werden.
- Modellfehlalarme (false positives) werden berwacht, um nicht unntig Wartung auszulsen.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Plan maintenance windows based on predicted failures | M2 | Reduzierte ungeplante Stillstnde, stabilere OEE |
| Auto-dispatch technicians and parts to high-risk assets | L2 | Bessere Ressourcenauslastung, krzere MTTR |
| Adjust maintenance strategy based on asset criticality and failure patterns | O2 | Geringere Gesamtwartungskosten bei gleichbleibender Verfgbarkeit |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Overall Equipment Effectiveness (OEE) %, Availability %, Downtime Hours, Machine Downtime % with Plan/LY deltas.
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
- Predictive-Model-Details (Feature Engineering, Algorithmus) liegen auerhalb dieses FactSheets; hier werden primr KPIs und Datenanforderungen beschrieben.
- Auto-Dispatch erzeugt Vorschlge (z.B. Assign Technician X at Slot Y"); Umsetzung kann ber externe Systeme (CMMS, FSM) erfolgen.
- Nicht alle Assets mssen initial abgedeckt werden; Start mit kritischen Anlagen/Familien.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Availability | Weniger ungeplante Downtime | Downtime Hours, Machine Downtime % |
| Efficiency | Besser ausgelastete Techniker, weniger Express-Beschaffungen | Wartungskosten, Techniker-Produktivitt |
| Capacity | Hhere Produktionsverfgbarkeit und Durchsatz | OEE %, Performance % |