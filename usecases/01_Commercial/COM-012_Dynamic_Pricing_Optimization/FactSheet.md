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

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
