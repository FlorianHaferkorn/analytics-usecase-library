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
