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