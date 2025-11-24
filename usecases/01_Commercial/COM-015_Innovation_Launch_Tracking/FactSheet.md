---
id: "COM-015"
title: "Innovation Launch Tracking"
domain: "Commercial"
owner: "Head of Innovation / Category Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Innovation Rate %"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "people.innovation_rate.pct"]
action_codes: ["I2", "P2", "SP1"]
expected_impact: "Track distribution, offtake and repeat for new products to improve launch success and de-list weak innovations faster."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Channel",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["Innovation_Flag_Consistent", "Lifecycle_Stage_Defined"]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "margin.gm.pct",
    "people.innovation_rate.pct",
    "people.new_product_share",
    "prod.lifecycle.new_share.pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
  people.innovation_rate.pct: "Innovation Rate %"
  people.new_product_share: "New Product Share"
  prod.lifecycle.new_share.pct: "New Product Share % in Lifecycle"
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
        - { name: "Is New Product", type: bool, role: indicator }
    - name: fact_product_lifecycle
      grain: product_period
      primary_key: [ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Lifecycle Stage", type: string, role: attribute }
        - { name: "New Flag", type: bool, role: indicator }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Channel, type: string }
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
    - { from: fact_product_lifecycle.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_product_lifecycle.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Lifecycle Stage": "fact_product_lifecycle[Lifecycle Stage]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Innovation Launch Tracking

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
