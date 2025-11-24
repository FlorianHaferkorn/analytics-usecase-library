# On-Shelf Availability & Stockout Root Causes - Business Factsheet

## 1. Summary
- **Business Goal:** Increase on-shelf availability and avoid lost sales by understanding where stockouts are generated along the supply chain and which root causes dominate.
- **Target Audience:** Head of Supply Chain / Retail Operations
- **Business Priority:** High
- **Expected Impact:** Improve on-shelf availability by identifying where along the supply chain stockouts are created and which actions prevent lost sales.

## 2. Core Questions
- Wo (Region, Store, Kategorie) treten die meisten Stockouts auf und wie gro ist der resultierende Umsatzverlust?
- Welche Root Causes dominieren: Forecast-Fehler, falsche Bestellmengen, Kommissionierfehler, Transportverzgerungen oder In-Store-Handling?
- Welche Kombination aus Manahmen (Parameteranpassungen, Prozessnderungen, Training) liefert den grten Service-Level-Gewinn?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Order Accuracy % | Correctly picked/shipped order lines / Total order lines | % |
| Net Sales Amount | Sales revenue, used to quantify lost sales | EUR |

## 4. Business Logic & Thresholds
- Returns, Stornos und Nachlieferungen mssen je nach Definition in Order-/Service-KPIs korrekt bercksichtigt werden.
- Datenqualitt in logistischen Events (z.B. Fehlbuchungen) kann Root-Cause-Analysen verzerren und sollte berwacht werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Adjust replenishment rules and safety stock for chronic stockout SKUs | I1 | Weniger Stockouts bei kritischen Artikeln |
| Improve order accuracy and picking processes in warehouses | I2 | Hhere Service-Level und weniger Fehlerkosten |
| Remove or redesign promotions that systematisch zu Stockouts fhren | D1 | Stabilere Verfgbarkeit bei Aktionen |
| Establish joint Commercial-Supply Chain reviews for stockout hotspots | O2 | Bessere end-to-end Abstimmung und nachhaltigere Lsungen |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Stockout Rate %, On-Time-In-Full (OTIF) %, Order Accuracy %, Net Sales Amount with Plan/LY deltas.
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
- Stockout-Definition (z.B. nicht verfgbar zum Zeitpunkt der Nachfrage") ist klar dokumentiert und technisch abbildbar (Order Lines, Store-Inventory).
- Root-Cause-Codes (z.B. Forecast, Picking, Transport, Shelf) knnen nach und nach ergnzt werden; initial reichen Service- und Prozess-KPIs.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Hhere on-shelf availability und OTIF | Stockout Rate %, OTIF % |
| Revenue | Weniger lost sales durch Stockouts | Umsatzentwicklung in Hotspot-Segmenten |
| Efficiency | Weniger manuelle Firefighting-Aktivitten | Anzahl Ad-hoc-Expedite / Notfallaktionen |
