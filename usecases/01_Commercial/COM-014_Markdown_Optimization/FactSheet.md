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

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
