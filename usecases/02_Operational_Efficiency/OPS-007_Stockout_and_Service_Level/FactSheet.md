---
id: "OPS-007"
title: "Stockout & Service Level"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Customer Service"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Working Capital %"]
supports_strategic_kpi_ids: ["ops.otif.pct", "ops.stockout.pct", "ops.working_capital.pct"]
action_codes: ["I1", "I2", "O2", "D1"]
expected_impact: "≥ 97–99 % service level with fewer stockouts and optimized inventory."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "OTIF_InRange", "Stockout_Events_Tracked"]
required_kpi_ids: [
  "ops.otif.pct",
  "ops.stockout.pct",
  "ops.order_accuracy.pct"
]
required_kpis:
  ops.otif.pct: "On-Time In-Full (OTIF) %"
  ops.stockout.pct: "Stockout Rate %"
  ops.order_accuracy.pct: "Order Accuracy %"
data_requirements:
  facts:
    - name: fact_orders
      grain: order_line
      primary_key: [OrderLineID]
      required_columns:
        - { name: OrderLineID, type: string, role: attribute }
        - { name: "Requested Date", type: date, role: date_key }
        - { name: "Delivered Date", type: date, role: helper }
        - { name: "Requested Qty", type: decimal, role: quantity }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Stockout Flag", type: bool, role: indicator }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_orders.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_orders.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_orders."Requested Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Requested Qty": "fact_orders[Requested Qty]"
  "Delivered Qty": "fact_orders[Delivered Qty]"
  "Stockout Flag": "fact_orders[Stockout Flag]"
  "Requested Date": "fact_orders[Requested Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Channel": "fact_orders[Channel]"
  "Date": "dim_date[Date]"
---

# Stockout & Service Level

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
