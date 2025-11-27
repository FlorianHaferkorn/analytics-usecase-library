---
id: "OPS-018"
title: "Route Optimization & Transport Cost Modeling"
domain: "Operational Efficiency"
owner: "Head of Logistics / Transport Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Operating Cost Ratio %", "Service Level %"]
supports_strategic_kpi_ids:
  ["ops.logistics.cost_ratio.pct", "ops.otif.pct"]
action_codes: ["O2", "I1", "PC2"]
expected_impact: "Reduce transport cost while maintaining service level by optimizing routes, loads and transport modes based on demand and constraints."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>DC",
    "Transport.Route>Stop",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 13W", "Org: All"]
qa_asserts: ["Transport_Cost_Allocation_Documented", "Route_Master_Consistent"]
required_kpi_ids:
  [
    "ops.logistics.cost_ratio.pct",
    "ops.logistics.cost_per_unit.amount",
    "ops.otif.pct",
  ]
required_kpis:
  ops.logistics.cost_ratio.pct: "Logistics Cost Ratio %"
  ops.logistics.cost_per_unit.amount: "Logistics Cost per Unit"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
data_requirements:
  facts:
    - name: fact_transport
      grain: shipment
      primary_key: [ShipmentID]
      required_columns:
        - { name: ShipmentID, type: string, role: attribute }
        - { name: "Route ID", type: string, role: attribute }
        - { name: "Departure Date", type: date, role: date_key }
        - { name: "Transport Cost Amount", type: decimal, role: amount }
        - { name: "Shipped Units Qty", type: decimal, role: quantity }
        - { name: "Distance Km", type: decimal, role: attribute }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: "Distribution Center", type: string }
    - name: dim_route
      grain: route
      primary_key: ["Route ID"]
      required_columns:
        - { name: "Route Name", type: string }
        - { name: "Transport Mode", type: string }
  relationships:
    - { from: fact_transport."Departure Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    # OrgID may come from DC or shipping org, simplified here
model_mapping:
  "Transport Cost Amount": "fact_transport[Transport Cost Amount]"
  "Shipped Units Qty": "fact_transport[Shipped Units Qty]"
  "Distance Km": "fact_transport[Distance Km]"
  "Route ID": "fact_transport[Route ID]"
  "Route Name": "dim_route[Route Name]"
  "Date": "dim_date[Date]"
---

# Route Optimization & Transport Cost Modeling - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize transport routes, modes and loads to reduce logistics cost per unit and cost ratio while maintaining agreed service levels (OTIF).
- **Target Audience:** Head of Logistics / Transport Planning
- **Business Priority:** High
- **Expected Impact:** Reduce transport cost while maintaining service level by optimizing routes, loads and transport modes based on demand and constraints.

## 2. Core Questions
- Welche Routen, Regionen oder Kunden verursachen die hchsten Transportkosten pro Einheit bzw. Kostenquote?
- Wo sind Laderaum- oder Kapazittsauslastung unzureichend - und welche Konsolidierungsmglichkeiten gibt es?
- Welche Alternativen (z.B. andere Mode, andere DC-Zuordnung, genderte Lieferrhythmen) verbessern Kosten und Service?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Logistics Cost Ratio % | Total logistics cost / Net Sales or shipped value | % |
| Logistics Cost per Unit | Transport cost / shipped units | EUR per unit |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |

## 4. Business Logic & Thresholds
- Leere oder sehr kleine Fahrten (z.B. Notfall-Lieferungen) werden gesondert ausgewiesen.
- Fehlende Kilometer-/Volumenangaben knnen pro Route geschtzt werden; Annahmen sind zu dokumentieren.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Redesign delivery frequencies and routes to improve load utilization | O2 | Weniger Leerfahrten, niedrigere Kosten/Einheit |
| Switch modes for geeignete Strecken (z.B. Strae  Bahn/See) | I1 | Geringere Kosten und ggf. CO-Emissionen |
| Renegotiate contracts based on transparent cost-per-route information | PC2 | Bessere Einkaufskonditionen fr Transporte |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Logistics Cost Ratio %, Logistics Cost per Unit, On-Time-In-Full (OTIF) % with Plan/LY deltas.
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
- Cost Allocation (z.B. fix vs variabel, Handling vs Linehaul) ist dokumentiert; initial reicht Transportkostensumme je Shipment.
- Service-Level (OTIF) wird separat erfasst; hier liegt Fokus auf Kostenseite und Basis-Service.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Cost | 5-15 % niedrigere Transportkosten bei stabilem Service | Logistics Cost Ratio %, Cost per Unit |
| Efficiency | Besser ausgelastete Fahrzeuge und Routen | Load Factor, Fahrten pro Tag/Woche |