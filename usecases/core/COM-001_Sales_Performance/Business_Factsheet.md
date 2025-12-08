# COM-001 – Business Factsheet

## 1. Summary
- **Business Goal:** Measure and explain deviations in Net Sales vs Plan and Last Year, and identify the main growth drivers (price, volume, mix, channel, region).
- **Target Audience:** Executive (CCO, CFO), Sales Management, Commercial Controlling.
- **Business Priority:** High.
- **Expected Impact:** Earlier detection of negative trends, targeted corrective actions on price, mix, channel and region; improved revenue growth and gross margin stability.

## 2. Core Questions
- Where do Net Sales deviate most vs Plan and vs Last Year?
- What are the key drivers of Δ Net Sales (price, volume, mix)?
- Which regions/channels/products underperform?
- Welche Maßnahmen (Preise, Promo, Bestand) schließen die Lücken?

## 3. KPI Set (Business View)

| KPI Name               | Purpose                         | Definition                                                | Interpretation                        | Decision Relevance |
|------------------------|----------------------------------|------------------------------------------------------------|----------------------------------------|--------------------|
| Net Sales Amount       | Commercial performance           | Invoice-level net revenue                                 | ↑ = stronger sales                     | Primäre Steuergröße |
| Revenue Growth %       | Growth vs LY                     | (NS – NS LY) / NS LY                                      | Wachstumsindikator                    | Forecast, Planung   |
| Sales vs Plan %        | Target deviation                 | (NS – Plan) / Plan                                        | >0 = Übererfüllung                     | Steuerung           |
| Gross Margin %         | Margin quality behind sales      | (Net Sales – COGS) / Net Sales                            | Leakage bei GM% ↓                      | Maßnahmenbedarf     |
| Price/Volume/Mix Effect| Treiber der Δ Net Sales          | Preis-, Mengen-, Mixeffekt                                | Dominanter Treiber ersichtlich         | Aktionsempfehlungen |

## 4. Business Logic & Thresholds
- Revenue Growth % < 0 % über 2 Perioden = kritischer Trend.
- Sales vs Plan % < −5 % = Management-Aufmerksamkeit.
- GM % signifikant unter Ziel = Pricing-/Mixproblem.
- Price Effect negativ & Volume stabil = Preissensitivität.
- Volume negativ & Price positiv = Nachfrage-/Kanalproblem.

## 5. Action Codes (Business Perspective)

| Code | Name                  | Beschreibung                               | Trigger                                  | Effekt |
|------|-----------------------|---------------------------------------------|-------------------------------------------|--------|
| P1   | Price Review          | Überprüfung und Anpassung von Listen-/Nettopreisen | negativer Price Effect             | GM-Stabilisierung |
| P2   | Discount Optimization | Reduktion unerwünschter Rabatte             | hohe Rabattquote                          | weniger Leakage |
| D1   | Demand Stimulation    | Impulse in Schwachregionen                  | negativer Volume Effect                   | höherer Absatz |
| I1   | Inventory Rebalancing | Bestandsumlagerung                           | wiederholte Out-of-Stocks                 | weniger Sales-Verlust |

## 6. 3–30–300 Page Layout

### 6.1 3-Second Layer
- KPI Cards (Sales, ΔYoY %, ΔPlan %, GM %, Drivers)

### 6.2 30-Second Layer
- Region/Channel/Product Rankings (horizontal bar)
- 12–24M Sales Trend (Line)
- Price/Volume/Mix Waterfall

### 6.3 300-Second Layer
- Drilldowns (Region → Country → Customer)
- Kategorien-/Produktmatrix
- KPI export

## 7. Dependencies & Constraints
- Planwerte notwendig
- stabile Hierarchien
- Promotions optional, aber sinnvoll

## 8. Success Criteria
- Einheitliches KPI-Verständnis
- 80 % Nutzung in Sales Reviews
- Dokumentierte Action Codes
