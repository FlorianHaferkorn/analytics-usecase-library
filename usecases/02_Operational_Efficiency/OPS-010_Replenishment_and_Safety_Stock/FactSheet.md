---
id: "OPS-010"
title: "Replenishment & Safety Stock"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Service Level %", "Inventory Days", "Stock-Out Rate %"]
supports_strategic_kpi_ids: ["ops.otif.pct", "ops.inventory.days", "ops.stockout.pct"]
action_codes: ["I1", "I2", "SP1"]
expected_impact: "+2–3 pp service level with -5–10 % inventory value."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All"
]
qa_asserts: ["RI_OK", "ServiceLevel_Bounds", "LeadTime_Positive"]
required_kpi_ids: [
  "ops.inventory.days",
  "ops.stockout.pct",
  "ops.otif.pct",
  "ops.order_accuracy.pct"
]
required_kpis:
  ops.inventory.days: "Inventory Days"
  ops.stockout.pct: "Stockout Rate %"
  ops.otif.pct: "OTIF %"
  ops.order_accuracy.pct: "Order Accuracy %"
data_requirements:
  facts:
    - name: fact_inventory
      grain: sku_location_day
      primary_key: [InventoryID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "On Hand Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
    - name: fact_demand
      grain: sku_location_day
      primary_key: [DemandID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Demand Qty", type: decimal, role: quantity }
    - name: fact_replenishment
      grain: sku_location_day
      primary_key: [ReplenishmentID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Planned Order Qty", type: decimal, role: quantity }
        - { name: "Received Qty", type: decimal, role: quantity }
        - { name: "Lead Time Days", type: decimal, role: helper }
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
        - { name: Week, type: int }
  relationships:
    - { from: fact_inventory.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_inventory.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_demand.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_demand.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_demand.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "On Hand Qty": "fact_inventory[On Hand Qty]"
  "Safety Stock Qty": "fact_inventory[Safety Stock Qty]"
  "Demand Qty": "fact_demand[Demand Qty]"
  "Planned Order Qty": "fact_replenishment[Planned Order Qty]"
  "Received Qty": "fact_replenishment[Received Qty]"
  "Lead Time Days": "fact_replenishment[Lead Time Days]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
---

# Replenishment & Safety Stock

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
