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

# Route Optimization & Transport Cost Modeling

## 1. Business Goal
Optimize transport routes, modes and loads to reduce logistics cost per unit and cost ratio while maintaining agreed service levels (OTIF).

---

## 2. Business Context
Transport ist einer der größten OPEX-Blöcke in vielen Unternehmen.  
Routen sind historisch gewachsen, Laderaumauslastung und Modewahl (Straße, Luft, See) sind oft nicht optimal und werden selten datengetrieben überprüft.  
Dieser Use Case stellt KPIs für Kosten und Service entlang von Routen und Stopps bereit und bildet die Grundlage für Optimierungsmodelle (z.B. Netzwerkanalyse, Vehicle Routing).

---

## 3. Key Questions
- Welche Routen, Regionen oder Kunden verursachen die höchsten Transportkosten pro Einheit bzw. Kostenquote?
- Wo sind Laderaum- oder Kapazitätsauslastung unzureichend – und welche Konsolidierungsmöglichkeiten gibt es?
- Welche Alternativen (z.B. andere Mode, andere DC-Zuordnung, geänderte Lieferrhythmen) verbessern Kosten und Service?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Logistics Cost Ratio % | Total logistics cost / Net Sales or shipped value | % |
| Logistics Cost per Unit | Transport cost / shipped units | EUR per unit |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |

---

## 5. Required Attributes (Business-Level)
- Org: Region, Distribution Center.
- Route: ID, Name, Mode, Stop-Sequenz.
- Time: Week, Month.
- Volumen: Units, ggf. Gewicht/Volumen.

---

## 6. Segmentation & Hierarchies
- Org: Region > DC.
- Route: Mode > Route > Stop.
- Time: Year > Month > Week.

---

## 7. Scope & Assumptions
- Cost Allocation (z.B. fix vs variabel, Handling vs Linehaul) ist dokumentiert; initial reicht Transportkostensumme je Shipment.
- Service-Level (OTIF) wird separat erfasst; hier liegt Fokus auf Kostenseite und Basis-Service.

---

## 8. Data Freshness & Cadence
- Transportdaten: täglich oder nach Batch-Import.
- Reporting: wöchentlich/monatlich für Logistik- und Finance-Reviews.

---

## 9. Edge Cases & QA Rules
- Leere oder sehr kleine Fahrten (z.B. Notfall-Lieferungen) werden gesondert ausgewiesen.
- Fehlende Kilometer-/Volumenangaben können pro Route geschätzt werden; Annahmen sind zu dokumentieren.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Transportkosten und Units je Shipment/Route/Periode.
  - Route-Masterdaten (Mode, Route-ID).
- Optional:
  - Service-Level-Details, CO₂-Emissionen, Mautkosten etc.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Redesign delivery frequencies and routes to improve load utilization | O2 | Weniger Leerfahrten, niedrigere Kosten/Einheit |
| Switch modes for geeignete Strecken (z.B. Straße → Bahn/See) | I1 | Geringere Kosten und ggf. CO₂-Emissionen |
| Renegotiate contracts based on transparent cost-per-route information | PC2 | Bessere Einkaufskonditionen für Transporte |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Cost | 5–15 % niedrigere Transportkosten bei stabilem Service | Logistics Cost Ratio %, Cost per Unit |
| Efficiency | Besser ausgelastete Fahrzeuge und Routen | Load Factor, Fahrten pro Tag/Woche |

---

## 13. Related Processes
Network Design -> Route & Frequency Planning -> Carrier Selection & Tendering -> Transport Execution -> Performance Review.

---

## 14. Insights & Learnings
Typisch ist, dass ein kleiner Anteil von Routen und Kunden einen Großteil der Transportkosten verursacht und dass durch leichte Anpassungen (z.B. Zusammenlegung von Touren) erhebliche Einsparungen möglich sind.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-009 Logistics Cost Ratio](../OPS-009_Logistics_Cost_Ratio/FactSheet.md)`  
  `[OPS-017 OTIF Root Cause Analysis](../OPS-017_OTIF_Root_Cause_Analysis/FactSheet.md)`  
  `[ESG-002 Energy Efficiency Optimization](../../05_ESG/ESG-002_Energy_Efficiency_Optimization/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Logistics / Transport Planning] |
| Technical Reviewer | [Transport Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first route optimization projects] |

---

_Last updated: 19.11.2025_

