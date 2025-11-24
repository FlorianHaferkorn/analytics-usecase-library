# OTIF Root Cause Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** Improve OTIF performance by identifying and quantifying the main root causes of delivery failures across the end-to-end supply chain.
- **Target Audience:** Head of Logistics / Supply Chain
- **Business Priority:** High
- **Expected Impact:** Explain OTIF deviations by root causes across planning, warehouse, transport and customer processes, and prioritize corrective actions.

## 2. Core Questions
- Wie unterscheiden sich OTIF-Werte nach Region, DC, Kunde und Segment?
- Welche Root Causes (z.B. Planungsfehler, Pickingfehler, Transportverzgerungen) dominieren?
- Welche Kunden- oder Produktsegmente sind besonders anfllig fr OTIF-Probleme?
- Welche Manahmen haben die grte Wirkung auf OTIF - und in welchem Zeitrahmen?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly delivered lines / Total lines | % |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |

## 4. Business Logic & Thresholds
- Lieferungen mit unvollstndigen oder fehlenden Issue Codes werden separat ausgewiesen.
- Rcksendungen und Reklamationen sollten je nach Servicedefinition bercksichtigt werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Introduce targeted corrective actions for dominant root causes (e.g., picking process changes) | I1 | Deutliche Verbesserung der OTIF-Werte in betroffenen Bereichen |
| Align planning and cut-off times with transport and customer constraints | I2 | Weniger versptete Lieferungen |
| Adjust customer and SLA settings for strukturell kritische Kombinationen | O2 | Realistischere Service-Level und weniger Vertragsstrafen |
| Remove or redesign processes that regelmig Fehler verursachen | D1 | Weniger systematische OTIF-Probleme |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for On-Time-In-Full (OTIF) %, Order Accuracy %, Stockout Rate % with Plan/LY deltas.
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
- OTIF-Definition (z.B. Toleranzfenster fr On-Time") ist klar dokumentiert.
- Root-Cause-Codes sind standardisiert und werden im Lieferprozess erfasst.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Hhere OTIF-Werte und bessere Kundenzufriedenheit | OTIF %, Service-Level-Feedback |
| Cost | Weniger Eilauftrge, Strafzahlungen und Reklamationen | Sonderkosten, Penalties |
| Efficiency | Weniger Firefighting und Ad-hoc-Lsungen | Anzahl Notfallaktionen, Stabilitt im Lieferprozess |
