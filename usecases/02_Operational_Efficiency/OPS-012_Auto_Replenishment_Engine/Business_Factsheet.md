# Auto-Replenishment Engine - Business Factsheet

## 1. Summary
- **Business Goal:** Automate replenishment decisions by proposing optimal order quantities and timings per SKU/location to meet target service levels while minimizing inventory days and working capital.
- **Target Audience:** Head of Supply Chain / Demand Planning
- **Business Priority:** High
- **Expected Impact:** Automate replenishment decisions by proposing optimal order quantities and timings per SKU/location, balancing service level and working capital.

## 2. Core Questions
- Welche SKUs/Standorte sind aktuell ber- bzw. unterversorgt im Vergleich zum Zielbestand?
- Wie gut treffen unsere bisherigen Replenishment-Regeln die definierte Service-Level-Zielgre?
- Welche Bestellvorschlge ergeben sich aus einem datengetriebenen Algorithmus (z.B. (R,Q)-Policy, Safety-Stock-Formeln)?
- Wo weichen Planner-Entscheidungen systematisch von den Vorschlgen ab - und mit welchen Effekten auf Service und Bestnde?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| Stockout Rate % | Stockout Order Lines / Total Order Lines | % |
| Replenishment Plan Adherence % | 1 - |Actual - Planned| / Planned Orders | % |
| Order Accuracy % | Correctly fulfilled orders / Total orders | % |
| OTIF % | On-Time-In-Full deliveries / Total deliveries | % |
| Forecast Accuracy (MAPE %) | MAPE von Forecast vs Actual Units | % |

## 4. Business Logic & Thresholds
- SKUs ohne belastbare Historie oder Forecast werden mit konservativer Policy (z.B. manuelle Freigabe) behandelt.
- Negative Bestnde und fehlerhafte Buchungen werden vor der Berechnung bereinigt oder ausgeschlossen.
- Service-Level-KPI-Berechnungen werden auf definierte Zeitfenster und Segmente begrenzt (z.B. Ausschluss von Launchartikeln in den ersten Wochen).

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Implement auto-generated order proposals for defined SKU classes | W1 | Reduzierte Bestandsstreuung, weniger Stockouts |
| Adjust Min/Max and safety-stock parameters based on algorithm output | P2 | Bessere Balance zwischen DIO und Service-Level |
| Escalate exceptions (z.B. Kapazitts- oder Supplier-Limits) in S&OP-Prozess | O2 | Hhere Planbarkeit und weniger Ad-hoc-Firefighting |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Days on Hand (DIO), Inventory Turnover, Stockout Rate %, Replenishment Plan Adherence %, Order Accuracy % with Plan/LY deltas.
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
- Die Engine erzeugt Bestellvorschlge (z.B. Order Qty" je SKU/Site/Day); finale Entscheidungen liegen weiterhin beim Planner.
- Lead Times, Min/Max und Service-Level-Ziele sind zentral gepflegt und werden regelmig berprft.
- Algorithmus-Variante (z.B. klassische Safety-Stock-Formel, Croston, Machine Learning) kann je Reifegrad variieren, beeinflusst aber nicht die KPI-Logik.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Service Level | Weniger Stockouts bei kritischen SKUs | Stockout Rate %, OTIF |
| Efficiency | Weniger manuelle Dispoprozesse | Anzahl manuell disponierter SKUs, Planerzeit |
| Liquidity | Reduktion von berbestnden bei stabilen Service Levels | DIO, Inventory Turnover |
