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
