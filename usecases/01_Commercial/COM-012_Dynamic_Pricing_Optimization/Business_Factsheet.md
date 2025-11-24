# Dynamic Pricing Optimization - Business Factsheet

## 1. Summary
- **Business Goal:** Dynamically optimize prices across channels, regions and products to achieve a better balance between revenue growth and gross margin, while respecting competitive context and inventory constraints.
- **Target Audience:** Head of Pricing / Revenue Management
- **Business Priority:** High
- **Expected Impact:** Optimize prices dynamically across channels and products to balance revenue growth and gross margin, based on price elasticity, competition and inventory.

## 2. Core Questions
- In welchen Segmenten und Produkten besteht Preisspielraum nach oben, ohne Volumen stark zu gefhrden?
- Wo sind wir systematisch zu gnstig oder zu teuer im Vergleich zu Wettbewerb und historischer Preisrealisation?
- Welche Preisempfehlungen ergeben sich aus Elastizitts- und Nachfrageprognosen, insbesondere in Verbindung mit Promotions und Inventory?
- Wie stark verbessern sich GM % und Revenue, wenn empfohlene Anpassungen umgesetzt werden?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Price Realization % | Net Sales / List Price Amount | % |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % |

## 4. Business Logic & Thresholds
- Produkte mit geringer Datenbasis oder sehr volatilen Verkufen werden von aggressiven Preisempfehlungen ausgenommen.
- Preisuntergrenzen (Floor-Prices, regulatorische Grenzen) mssen im Modell verankert sein.
- Governance-Regeln definieren, welche Preisnderungen automatisch angenommen, welche eskaliert und welche verworfen werden.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Increase price in low-elasticity, high-margin segments | M3 | Hhere GM %, begrenzter Volumenverlust |
| Reduce price in highly elastic segments with spare capacity | P2 | Hheres Volumen/Revenue bei akzeptabler GM |
| Remove or redesign structurally unprofitable promos | D1 | Reduzierte Margenerosion, stabilere Preise |
| Introduce governance and approval workflows for price changes | SP1 | Konsistentere Preisstrategie, weniger Ad-hoc-Rabatte |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Gross Margin %, Price Realization %, Promo Uplift % with Plan/LY deltas.
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
- Dynamic Pricing gibt Empfehlungen (z.B. % Anpassung vom aktuellen Preis); Umsetzung erfolgt nach Governance-Prozess.
- Elastizitten werden aus historischen Preis-/Volumen-Mustern geschtzt; nderungen auerhalb des beobachteten Bereichs sind mit Vorsicht zu interpretieren.
- Promotions werden getrennt von Listenpreis-Entscheidungen betrachtet, um Effekte nicht zu vermischen.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Verbesserte GM % und stabilere Margen | GM %, Preisrealisierung % |
| Growth | Zustzlicher Umsatz in gezielt unterpreisigen Segmenten | Revenue vs Plan/LY |
| Governance | Weniger unkontrollierte Rabatte; konsistente Preislogik | Anteil Governance-konformer Preisentscheidungen |
