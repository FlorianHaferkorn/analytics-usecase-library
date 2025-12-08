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