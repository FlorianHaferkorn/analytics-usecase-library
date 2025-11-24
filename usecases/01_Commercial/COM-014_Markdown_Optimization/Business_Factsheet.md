# Markdown Optimization - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize markdown timing and depth across categories and stores to clear inventory at the best possible margin and avoid excessive end-of-season stock.
- **Target Audience:** Head of Pricing / Category Management
- **Business Priority:** High
- **Expected Impact:** Optimize markdown timing and depth to maximize sell-through while minimizing margin leakage and residual inventory.

## 2. Core Questions
- Welche Artikel und Kategorien bentigen Markdown, um Saison-/Aktionsziele zu erreichen?
- Wann ist der beste Zeitpunkt fr Markdown, um Abverkauf und Marge zu optimieren?
- Wie wirkt sich Markdown-Tiefe auf Volumen, Marge und Restbestnde aus?
- Welche Kampagnen mit Markdown-Anteil waren profitabel, welche nicht?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue per SKU/Store/Period | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| List Price Amount | Value at list price | EUR |
| Price Realization % | Net Sales / List Price Amount | % |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |

## 4. Business Logic & Thresholds
- Launch-SKUs mit wenig Historie werden vorsichtig behandelt; initiale Markdown-Entscheidungen knnen auf Kategorieebene erfolgen.
- Extreme Preisnderungen oder Datenfehler werden gefiltert, bevor Elastizitten oder Uplifts berechnet werden.
- Saisondefinitionen und Kalender mssen sauber gepflegt sein, damit KPIs korrekt interpretiert werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Plan structured markdown waves per category and season | P2 | Hherer planbarer Sell-through, weniger Restanten |
| Adjust markdown depth per SKU cluster based on productivity | M3 | Geringerer Margin-Leakage bei gleichem Abverkauf |
| Delist structurally weak SKUs after repeated markdown cycles | D1 | Weniger Komplexitt und Abschreibungen |
| Align replenishment and markdown plans to reduce end-of-season stock | W1 | Niedrigere DIO zum Saisonende |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Gross Margin %, List Price Amount, Price Realization %, Promo Uplift % with Plan/LY deltas.
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
- Markdown wird ber Promo-Flags, Preisbnder oder explizite Markdown-Kennzeichnung identifiziert.
- Baseline Sales (ohne Markdown) knnen historisch oder modellbasiert (Forecast) ermittelt werden.
- Entscheidungen bercksichtigen zustzlich qualitative Faktoren (z.B. Markenimage, Wettbewerbsposition).

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Geringere Margin-Leakage bei Markdown-Aktionen | GM %, Preisrealisierung % |
| Working Capital | Reduzierte Restbestnde und Abschreibungen | DIO, Abschreibungen/Season-End |
| Process | Mehr Planbarkeit und weniger Ad-hoc-Markdowns | Anteil geplanter vs Ad-hoc-Markdowns |
