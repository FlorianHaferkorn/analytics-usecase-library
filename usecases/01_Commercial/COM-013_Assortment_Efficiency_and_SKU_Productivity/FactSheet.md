---
id: "COM-013"
title: "Assortment Efficiency & SKU Productivity"
domain: "Commercial"
owner: "Head of Category Management / Merchandising"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "margin.gm.pct", "fin.liquidity.working_capital"]
action_codes: ["P2", "M3", "D1", "W1"]
expected_impact: "Optimize assortment and shelf space by focusing on high-productivity SKUs and reducing low-performing items, improving margin and inventory efficiency."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Store",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Product_Hierarchy_Consistent", "Inventory_Valuation_Reconciles"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.pct",
    "ops.inventory.turnover",
    "ops.inventory.days",
    "sales.customer.revenue_share.pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  sales.customer.revenue_share.pct: "Customer Revenue Share %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Amount", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
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
  "Units Qty": "fact_sales[Units Qty]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Assortment Efficiency & SKU Productivity

## 1. Business Goal
Improve assortment efficiency and shelf productivity by identifying which SKUs drive most of the revenue and margin, and which consume space and working capital without sufficient contribution.

---

## 2. Business Context
Retail- und FMCG-Portfolios enthalten häufig sehr viele SKUs, von denen nur ein Teil den wesentlichen Beitrag zu Umsatz, Marge und Category-Performance leistet.  
Gleichzeitig binden schwach performende SKUs Regalfläche, Lagerkapazitäten und Working Capital.  
Dieser Use Case gibt Category Management und Sales eine faktenbasierte Grundlage zur Sortimentsbereinigung und Flächenallokation.

---

## 3. Key Questions
- Welche SKUs und Subkategorien tragen überproportional zu Umsatz und Marge bei?
- Welche SKUs haben niedrige Produktivität (z.B. Umsatz/m oder Marge/m²) bei gleichzeitig hohem Bestandsniveau?
- Welche Sortimentsbereinigungen wirken sich minimal auf Umsatz aus, reduzieren aber deutlich Bestände und Komplexität?
- Welche Lücken im Sortiment (White Spots) werden sichtbar, wenn schwache SKUs entfernt werden?

---

## 4. Key KPIs
| KPI | Definition | Unit |
|-----|------------|------|
| Net Sales Amount | Sales revenue per SKU/Store | EUR |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % |
| Inventory Turnover | COGS / Avg Inventory | ratio |
| Inventory Days (DIO) | Inventory / COGS * Days in Period | days |
| Customer Revenue Share % | SKU or segment revenue / total revenue | % |

---

## 5. Required Attributes (Business-Level)
- Product: Category, Subcategory, SKU.
- Org: Region, Store.
- Time: Month, Week.
- Optional: Shelf/Space attributes (z.B. Facings, Shelf m/ft) für erweiterte Productivity-KPIs.

---

## 6. Segmentation & Hierarchies
- Product: Category > Subcategory > SKU.
- Org: Region > Store.
- Time: Year > Month > Week.

---

## 7. Scope & Assumptions
- Sortimentsentscheidungen beziehen neben KPIs auch qualitative Aspekte (z.B. Markenstrategie, Lieferantenbeziehungen) ein.
- Inventurdaten sind ausreichend valide; extreme Ausreißer oder Datenfehler werden vor Analyse bereinigt.
- Shelf-/Flächeninformationen können später ergänzt werden; initialer Fokus liegt auf Umsatz/Marge vs Bestände.

---

## 8. Data Freshness & Cadence
- Sales: täglich/wöchentlich.
- Inventory: mindestens wöchentlich, ideal täglich auf Store/SKU-Level.
- Reporting: monatlich und quartalsweise für Sortimentsentscheidungen.

---

## 9. Edge Cases & QA Rules
- Neu eingeführte SKUs haben noch keine stabile Historie; Entscheidungskriterien werden entsprechend gekennzeichnet.
- SKUs mit stark saisonalem Muster sollten getrennt analysiert werden.
- Negative Margen (z.B. durch Fehlbuchungen oder extreme Discounts) werden überprüft und bereinigt.

---

## 10. Minimum Viable Dataset (MVD)
- Pflicht:
  - Sales nach SKU/Store/Periode.
  - Inventory-Bestände nach SKU/Store/Periode.
- Optional:
  - Shelf-/Planogrammdaten, um Flächenproduktivität auszuwerten.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|--------|------|-----------------|
| Delist low-productivity SKUs with minimal impact on category performance | D1 | Weniger Komplexität; reduzierte Bestände |
| Reallocate shelf space towards high-productivity SKUs | P2 | Höherer Umsatz/Marge je Flächeneinheit |
| Adjust ordering policies for slow movers | W1 | Reduktion von DIO; weniger Abschreibungen |
| Optimize assortment per store cluster | M3 | Besser an lokale Nachfrage angepasste Sortimente |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|-----------|-----------------|-------------|
| Profitability | Höhere Category-Marge durch Fokus auf produktive SKUs | GM %, Margin per SKU |
| Efficiency | Weniger Bestände und Abschreibungen | DIO, Abschreibungen/Beschädigungen |
| Complexity | Reduzierte SKU-Anzahl und Prozesskomplexität | # SKUs je Kategorie/Store |

---

## 13. Related Processes
Category Strategy & Role Definition -> Assortment Planning -> Space Planning -> Replenishment -> Performance Review.

---

## 14. Insights & Learnings
Typischerweise zeigt sich, dass 20–30 % der SKUs 70–80 % des Umsatzes und der Marge generieren, während viele SKUs kaum beitragen, aber Komplexität erzeugen. Zudem werden häufig Cluster sichtbar, in denen Sortimente nicht zur lokalen Nachfrage passen.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-003 Product Mix & Contribution](../COM-003_Promotion_Effectiveness/FactSheet.md)`  
  `[COM-006 Customer Profitability](../COM-006_Customer_Profitability/FactSheet.md)`  
  `[OPS-006 Inventory Turnover & DIO](../../02_Operational_Efficiency/OPS-006_Inventory_Turnover_and_DIO/FactSheet.md)`

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Head of Category Management] |
| Technical Reviewer | [Merchandising Analytics Lead] |
| Version | v0.1 |
| Review Date | DD.MM.YYYY |
| Review Notes | [To be filled after first assortment waves] |

---

_Last updated: 19.11.2025_

