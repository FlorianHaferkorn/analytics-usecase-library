---
id: "OPS-014"
title: "On-Shelf Availability & Stockout Root Causes"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Retail Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Revenue Growth %"]
supports_strategic_kpi_ids:
  ["ops.otif.pct", "sales.revenue.growth_pct"]
action_codes: ["I1", "I2", "D1", "O2"]
expected_impact: "Improve on-shelf availability by identifying where along the supply chain stockouts are created and which actions prevent lost sales."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>Store",
    "Product.Category>Subcategory>SKU",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12W", "Org: All"]
qa_asserts: ["Stockout_Definition_Documented", "Service_Level_Consistent"]
required_kpi_ids:
  [
    "ops.stockout.pct",
    "ops.otif.pct",
    "ops.order_accuracy.pct",
    "sales.net_sales.amount",
  ]
required_kpis:
  ops.stockout.pct: "Stockout Rate %"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  ops.order_accuracy.pct: "Order Accuracy %"
  sales.net_sales.amount: "Net Sales Amount"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
        - { name: "Order Lines OTIF", type: int, role: quantity }
        - { name: "Order Lines Accurate", type: int, role: quantity }
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
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Order Lines OTIF": "fact_service_level[Order Lines OTIF]"
  "Order Lines Accurate": "fact_service_level[Order Lines Accurate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# On-Shelf Availability & Stockout Root Causes

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
