---
id: "OPS-002"
title: "Inventory Health & Stock-Out Prevention"
domain: "Operational Efficiency"
owner: "Head of Supply Chain / Logistics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Working Capital %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "I2", "O2", "D1", "PC4"]
expected_impact: "-10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence"
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
qa_asserts: ["RI_OK", "Inventory_Value_Positive", "Coverage_InRange"]
required_kpi_ids: [
  "ops.inventory.days",
  "ops.stockout.pct",
  "ops.inventory.turnover",
  "ops.inventory.obsolescence.pct",
  "ops.otif.pct"
]
required_kpis:
  ops.inventory.days: "Inventory Days"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.turnover: "Inventory Turnover"
  ops.inventory.obsolescence.pct: "Obsolescence %"
  ops.otif.pct: "OTIF %"
data_requirements:
  facts:
    - name: fact_inventory_snapshot
      grain: sku_location_day
      primary_key: [SnapshotDate, OrgID, ProductID]
      required_columns:
        - { name: SnapshotDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Units", type: decimal, role: quantity }
        - { name: "Inventory Value", type: decimal, role: amount }
        - { name: "Demand Qty", type: decimal, role: quantity }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
        - { name: "Lead Time Days", type: int, role: helper }
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Warehouse, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_inventory_snapshot.SnapshotDate, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_inventory_snapshot.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory_snapshot.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Inventory Units": "fact_inventory_snapshot[Inventory Units]"
  "Inventory Value": "fact_inventory_snapshot[Inventory Value]"
  "Demand Qty": "fact_inventory_snapshot[Demand Qty]"
  "Delivered Qty": "fact_inventory_snapshot[Delivered Qty]"
  "Safety Stock Qty": "fact_inventory_snapshot[Safety Stock Qty]"
  "Lead Time Days": "fact_inventory_snapshot[Lead Time Days]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---
# Inventory Health & Stock-Out Prevention

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md) - Ziele, KPIs, Action Codes und 3-30-300 Layout.
- [Technical_Factsheet.md](./Technical_Factsheet.md) - Data Contract, Semantic Model, DAX, RLS und QA.

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
