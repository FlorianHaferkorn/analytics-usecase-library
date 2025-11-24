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
