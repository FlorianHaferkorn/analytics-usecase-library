---
id: "COM-014"
title: "Markdown Optimization"
domain: "Commercial"
owner: "Head of Pricing / Category Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "margin.gm.pct", "fin.liquidity.working_capital"]
action_codes: ["M3", "P2", "D1", "W1"]
expected_impact: "Optimize markdown timing and depth to maximize sell-through while minimizing margin leakage and residual inventory."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Store",
    "Product.Category>Subcategory>SKU",
    "Time.Season>Month>Week",
  ]
filters_default: ["Time: Current Season", "Org: All"]
qa_asserts: ["Season_Flag_Defined", "Markdown_vs_Base_Price_Separated"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.pct",
    "sales.list_price.amount",
    "sales.price.realization_pct",
    "sales.promo.uplift_pct",
    "ops.inventory.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
  sales.list_price.amount: "List Price Amount"
  sales.price.realization_pct: "Price Realization %"
  sales.promo.uplift_pct: "Promo Uplift %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
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
        - { name: ProductID, type: string, role: product_key }
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
        - { name: "Season", type: string, role: attribute }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
        - { name: Season, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Store, type: string }
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
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "List Price Amount": "fact_sales[List Price Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Markdown Optimization

## 1. Business Goal
Optimize markdown timing and depth across categories and stores to clear inventory at the best possible margin and avoid excessive end-of-season stock.

---

## 2. Business Context
In Fashion, DIY, Consumer Electronics und FMCG führen fixe Abverkaufstermine (Saisonende, Sortimentswechsel) häufig zu hektischen, nicht datenbasierten Markdown-Entscheidungen.  
Zu späte oder zu aggressive Markdown-Aktionen verursachen entweder hohe Restbestände oder unnötige Margenverluste.  
Dieser Use Case liefert eine strukturierte Sicht auf Sell-through, Preisrealisierung, Marge und Restbestände, um Markdown-Strategien datenbasiert zu planen und zu steuern.

---

## 3. Key Questions
- Welche Artikel und Kategorien benötigen Markdown, um Saison-/Aktionsziele zu erreichen?
- Wann ist der beste Zeitpunkt für Markdown, um Abverkauf und Marge zu optimieren?
- Wie wirkt sich Markdown-Tiefe auf Volumen, Marge und Restbestände aus?
- Welche Kampagnen mit Markdown-Anteil waren profitabel, welche nicht?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue per SKU/Store/Period | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| List Price Amount | Value at list price | EUR |
| Price Realization % | Net Sales / List Price Amount | % |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |

---

## 5. Required Attributes (Business-Level)
- Time: Season, Month, Week.
- Org: Region, Store.
- Product: Category, Subcategory, SKU.
- Price: List Price, Net Price (Net Sales / Units), Markdown Flag (via Promo/Season/Price Band).

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU.
- Org: Region > Store.
- Time: Year > Season > Month > Week.

---

## 7. Scope & Assumptions
- Markdown wird über Promo-Flags, Preisbänder oder explizite Markdown-Kennzeichnung identifiziert.
- Baseline Sales (ohne Markdown) können historisch oder modellbasiert (Forecast) ermittelt werden.
- Entscheidungen berücksichtigen zusätzlich qualitative Faktoren (z.B. Markenimage, Wettbewerbsposition).

---

## 8. Data Freshness & Cadence
- Sales: täglich/wöchentlich.
- Inventory: mindestens wöchentlich auf Store/SKU-Level.
- Markdown-Planung: typischerweise saisonal und in definierten Waves (z.B. Pre-Sale, Sale, Clearance).

---

## 9. Edge Cases & QA Rules
- Launch-SKUs mit wenig Historie werden vorsichtig behandelt; initiale Markdown-Entscheidungen können auf Kategorieebene erfolgen.
- Extreme Preisänderungen oder Datenfehler werden gefiltert, bevor Elastizitäten oder Uplifts berechnet werden.
- Saisondefinitionen und Kalender müssen sauber gepflegt sein, damit KPIs korrekt interpretiert werden.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales mit Preis- und Promo-Information auf SKU/Store/Periode.
  - Inventory-Bestände auf SKU/Store/Periode.
- Optional:
  - Wettbewerbs- und Marktpreisinfos.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Plan structured markdown waves per category and season | P2 | Höherer planbarer Sell-through, weniger Restanten |
| Adjust markdown depth per SKU cluster based on productivity | M3 | Geringerer Margin-Leakage bei gleichem Abverkauf |
| Delist structurally weak SKUs after repeated markdown cycles | D1 | Weniger Komplexität und Abschreibungen |
| Align replenishment and markdown plans to reduce end-of-season stock | W1 | Niedrigere DIO zum Saisonende |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Geringere Margin-Leakage bei Markdown-Aktionen | GM %, Preisrealisierung % |
| Working Capital | Reduzierte Restbestände und Abschreibungen | DIO, Abschreibungen/Season-End |
| Process | Mehr Planbarkeit und weniger Ad-hoc-Markdowns | Anteil geplanter vs Ad-hoc-Markdowns |

---

## 13. Related Processes
Seasonal Planning -> Assortment Planning -> Pricing & Markdown Planning -> Execution -> Post-Season Review.

---

## 14. Insights & Learnings
Typische Insights umfassen Kategorien mit strukturell zu späten oder zu tiefen Markdown-Aktionen, SKUs mit wiederholt schlechtem Abverkauf trotz starker Markdown-Budgets sowie Märkte, in denen Wettbewerbsdruck frühere Markdown-Wellen erfordert.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin Analysis](../COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COM-003 Product Mix & Contribution](../COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COM-005 Promotion ROI & Effectiveness](../COM-005_Promotion_ROI_and_Effectiveness/FactSheet.md)`  
  `[OPS-006 Inventory Turnover & DIO](../../02_Operational_Efficiency/OPS-006_Inventory_Turnover_and_DIO/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Pricing / Category Management] |
| Technical Reviewer | [Pricing Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first markdown waves] |

---

_Last updated: 19.11.2025_

