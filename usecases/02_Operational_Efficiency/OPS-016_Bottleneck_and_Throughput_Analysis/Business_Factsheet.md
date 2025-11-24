# Bottleneck & Throughput Analysis (TOC) - Business Factsheet

## 1. Summary
- **Business Goal:** Increase overall production throughput and shorten lead times by identifying and managing bottleneck resources according to the Theory of Constraints.
- **Target Audience:** Head of Operations / Plant Manager
- **Business Priority:** High
- **Expected Impact:** Identify and manage production bottlenecks to increase overall throughput without immediate CAPEX investments.

## 2. Core Questions
- Welche Anlage oder Linie ist der aktuelle Engpass im betrachteten Wertstrom?
- Wie stabil ist dieser Engpass ber Zeit - oder wandert er zwischen Ressourcen?
- Welche Manahmen (z.B. Schichtanpassung, Setup-Reduktion, Priorisierung) erhhen den Durchsatz am Engpass am strksten?
- Wie wirken sich Engpassmanahmen auf Gesamt-Output, OEE und Lieferzeiten aus?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| OEE % | Availability * Performance * Quality | % |
| Performance % | Actual Output / Theoretical Output | % |
| Produced Units Qty | Total units produced per asset/period | units |
| Good Units Qty | Good units produced (excl. scrap) per asset/period | units |

## 4. Business Logic & Thresholds
- Datenlcken bei Produktionsmengen oder OEE knnen Engpassanalyse verflschen; Qualittschecks sind ntig.
- Engpass kann sich bei greren Vernderungen (z.B. Produktmix, Nachfrage, CAPEX) verschieben und sollte regelmig neu bestimmt werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Elevate capacity at bottleneck resources (shifts, staffing) | M2 | Higher throughput, reduced backlog |
| Reduce setup and changeover on bottleneck lines | L2 | Mehr effektive Produktionszeit, weniger Micro-Stops |
| Re-sequence production to prioritize bottleneck utilization | SP1 | Krzere Durchlaufzeiten und stabilere Auslastung |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Overall Equipment Effectiveness (OEE) %, Performance %, Produced Units Qty with Plan/LY deltas.
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
- Wertstrom-Definition (Sequenz der Anlagen) ist bekannt; Engpassanalyse erfolgt pro Wertstrom.
- CAPEX-Beschrnkungen bedeuten, dass vorrangig Prozess- und Planungsmanahmen statt neuer Anlagen betrachtet werden.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Throughput | Hherer Output ohne sofortige CAPEX-Erhhung | Produced/Good Qty per period |
| Lead Time | Krzere Durchlaufzeiten im Wertstrom | Lead Time (Prozesssicht) |
| Cost | Bessere Fixkostendegression, geringere Stckkosten | Unit Cost, OEE |
