# Assortment Efficiency & SKU Productivity - Business Factsheet

## 1. Summary
- **Business Goal:** Improve assortment efficiency and shelf productivity by identifying which SKUs drive most of the revenue and margin, and which consume space and working capital without sufficient contribution.
- **Target Audience:** Head of Category Management / Merchandising
- **Business Priority:** High
- **Expected Impact:** Optimize assortment and shelf space by focusing on high-productivity SKUs and reducing low-performing items, improving margin and inventory efficiency.

## 2. Core Questions
- Welche SKUs und Subkategorien tragen berproportional zu Umsatz und Marge bei?
- Welche SKUs haben niedrige Produktivitt (z.B. Umsatz/m oder Marge/m) bei gleichzeitig hohem Bestandsniveau?
- Welche Sortimentsbereinigungen wirken sich minimal auf Umsatz aus, reduzieren aber deutlich Bestnde und Komplexitt?
- Welche Lcken im Sortiment (White Spots) werden sichtbar, wenn schwache SKUs entfernt werden?

## 3. KPI Set (Business View)
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue per SKU/Store | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Customer Revenue Share % | SKU or segment revenue / total revenue | % |

## 4. Business Logic & Thresholds
- Neu eingefhrte SKUs haben noch keine stabile Historie; Entscheidungskriterien werden entsprechend gekennzeichnet.
- SKUs mit stark saisonalem Muster sollten getrennt analysiert werden.
- Negative Margen (z.B. durch Fehlbuchungen oder extreme Discounts) werden berprft und bereinigt.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Delist low-productivity SKUs with minimal impact on category performance | D1 | Weniger Komplexitt; reduzierte Bestnde |
| Reallocate shelf space towards high-productivity SKUs | P2 | Hherer Umsatz/Marge je Flcheneinheit |
| Adjust ordering policies for slow movers | W1 | Reduktion von DIO; weniger Abschreibungen |
| Optimize assortment per store cluster | M3 | Besser an lokale Nachfrage angepasste Sortimente |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Gross Margin %, Inventory Turnover, Inventory Days on Hand (DIO), Customer Revenue Share % with Plan/LY deltas.
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
- Sortimentsentscheidungen beziehen neben KPIs auch qualitative Aspekte (z.B. Markenstrategie, Lieferantenbeziehungen) ein.
- Inventurdaten sind ausreichend valide; extreme Ausreier oder Datenfehler werden vor Analyse bereinigt.
- Shelf-/Flcheninformationen knnen spter ergnzt werden; initialer Fokus liegt auf Umsatz/Marge vs Bestnde.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Hhere Category-Marge durch Fokus auf produktive SKUs | GM %, Margin per SKU |
| Efficiency | Weniger Bestnde und Abschreibungen | DIO, Abschreibungen/Beschdigungen |
| Complexity | Reduzierte SKU-Anzahl und Prozesskomplexitt | # SKUs je Kategorie/Store |
