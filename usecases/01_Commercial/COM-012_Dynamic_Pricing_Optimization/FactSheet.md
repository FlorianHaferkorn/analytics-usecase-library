---
id: "COM-012"
title: "Dynamic Pricing Optimization"
domain: "Commercial"
owner: "Head of Pricing / Revenue Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["M3", "P2", "D1", "SP1"]
expected_impact: "Optimize prices dynamically across channels and products to balance revenue growth and gross margin, based on price elasticity, competition and inventory."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Channel",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Price_List_Consistent", "Promo_vs_Base_Price_Separated"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.pct",
    "sales.price.realization_pct",
    "sales.promo.uplift_pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
  sales.price.realization_pct: "Price Realization %"
  sales.promo.uplift_pct: "Promo Uplift %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "List Price Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: Channel, type: string, role: channel }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Promo Flag", type: bool, role: indicator }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: "Channel Group", type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "List Price Amount": "fact_sales[List Price Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Dynamic Pricing Optimization

## 1. Business Goal
Dynamically optimize prices across channels, regions and products to achieve a better balance between revenue growth and gross margin, while respecting competitive context and inventory constraints.

---

## 2. Business Context
Viele Unternehmen arbeiten mit statischen Preislisten und sporadischen Anpassungen (z.B. einmal pro Jahr), während Markt und Wettbewerb sich ständig ändern.  
Das führt zu verpassten Umsatzchancen in nachfragestarken Segmenten und zu unnötiger Margenerosion in preissensitiven Bereichen.  
Dynamic Pricing nutzt Elastizitätsmodelle, Wettbewerbsinformationen und Inventory-Signale, um datengestützte Preisempfehlungen abzugeben – die finale Entscheidung liegt weiterhin bei Pricing und Sales.

---

## 3. Key Questions
- In welchen Segmenten und Produkten besteht Preisspielraum nach oben, ohne Volumen stark zu gefährden?
- Wo sind wir systematisch zu günstig oder zu teuer im Vergleich zu Wettbewerb und historischer Preisrealisation?
- Welche Preisempfehlungen ergeben sich aus Elastizitäts- und Nachfrageprognosen, insbesondere in Verbindung mit Promotions und Inventory?
- Wie stark verbessern sich GM % und Revenue, wenn empfohlene Anpassungen umgesetzt werden?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Price Realization % | Net Sales / List Price Amount | % |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % |

---

## 5. Required Attributes (Business-Level)
- Time: Week, Month.
- Org: Region, Channel/Channel Group.
- Product: Category, Subcategory, SKU.
- Price Information: List Price, Net Price (via Net Sales / Units), Promo Flag.
- Optional: Wettbewerbsdaten (Preisvergleich, Promo-Intensität).

---

## 6. Segmentation & Hierarchies
- Time: Year > Month > Week.
- Org: Region > Channel > Account (optional).
- Product: Category > Subcategory > SKU.

---

## 7. Scope & Assumptions
- Dynamic Pricing gibt Empfehlungen (z.B. % Anpassung vom aktuellen Preis); Umsetzung erfolgt nach Governance-Prozess.
- Elastizitäten werden aus historischen Preis-/Volumen-Mustern geschätzt; Änderungen außerhalb des beobachteten Bereichs sind mit Vorsicht zu interpretieren.
- Promotions werden getrennt von Listenpreis-Entscheidungen betrachtet, um Effekte nicht zu vermischen.

---

## 8. Data Freshness & Cadence
- Sales-Daten: täglich/wöchentlich.
- Preislisten und Promo-Kalender: bei Änderungen, mindestens monatlich.
- Wettbewerbsdaten: abhängig von Datenquelle (Scraping, Syndicated Data).

---

## 9. Edge Cases & QA Rules
- Produkte mit geringer Datenbasis oder sehr volatilen Verkäufen werden von aggressiven Preisempfehlungen ausgenommen.
- Preisuntergrenzen (Floor-Prices, regulatorische Grenzen) müssen im Modell verankert sein.
- Governance-Regeln definieren, welche Preisänderungen automatisch angenommen, welche eskaliert und welche verworfen werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Historische Sales (Preis, Volumen) je SKU/Channel/Region.
  - List Price und ggf. Promo-Indikator.
- Optional:
  - Wettbewerbs- und Inventardaten zur weiteren Verfeinerung.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Increase price in low-elasticity, high-margin segments | M3 | Höhere GM %, begrenzter Volumenverlust |
| Reduce price in highly elastic segments with spare capacity | P2 | Höheres Volumen/Revenue bei akzeptabler GM |
| Remove or redesign structurally unprofitable promos | D1 | Reduzierte Margenerosion, stabilere Preise |
| Introduce governance and approval workflows for price changes | SP1 | Konsistentere Preisstrategie, weniger Ad-hoc-Rabatte |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Verbesserte GM % und stabilere Margen | GM %, Preisrealisierung % |
| Growth | Zusätzlicher Umsatz in gezielt unterpreisigen Segmenten | Revenue vs Plan/LY |
| Governance | Weniger unkontrollierte Rabatte; konsistente Preislogik | Anteil Governance-konformer Preisentscheidungen |

---

## 13. Related Processes
Pricing Strategy Definition -> Elasticity Modelling -> Price Recommendation Generation -> Approval & Execution -> Monitoring & Recalibration.

---

## 14. Insights & Learnings
Typische Learnings sind, dass einige Segmente deutlich weniger preissensitiv sind als angenommen, während andere sehr empfindlich reagieren. Zudem werden Promotions sichtbar, die überproportional viel Marge kosten im Vergleich zum Volumen- oder Revenue-Impact.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin Analysis](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COM-004 Price-Volume-Mix Bridge](../COM-004_Price_Volume_Mix_Bridge/FactSheet.md)`  
  `[COM-007 Price-Volume-Mix Bridge (Portfolio & Strategic View)](../COM-007_Price_Volume_Mix_Bridge/FactSheet.md)`  
  `[COM-003 Promotion Effectiveness (ROI & Uplift)](../COM-003_Promotion_Effectiveness/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Pricing / Revenue Management] |
| Technical Reviewer | [Pricing Analytics Lead / Data Scientist] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after pricing pilot] |

---

_Last updated: 19.11.2025_

