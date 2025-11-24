---
id: "OPS-004"
title: "Replenishment Optimization & Service Level Management"
domain: "Operational Efficiency"
owner: "Head of Supply Chain Planning"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Service Level %", "Stock-Out Rate %", "Inventory Days"]
supports_strategic_kpi_ids: ["ops.otif.pct", "ops.stockout.pct", "ops.inventory.days"]
action_codes: ["I1", "PC4", "I2", "O2", "SP1"]
expected_impact: "+2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Supplier.Group>Vendor",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "ServiceLevel_Bounds", "LeadTime_Positive"]
required_kpi_ids: [
  "ops.replenishment.adherence.pct",
  "ops.order_accuracy.pct",
  "ops.stockout.pct",
  "ops.inventory.days",
  "ops.otif.pct"
]
required_kpis:
  ops.replenishment.adherence.pct: "Replenishment Adherence %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.stockout.pct: "Stock-Out Rate %"
  ops.inventory.days: "Inventory Days"
  ops.otif.pct: "OTIF %"
data_requirements:
  facts:
    - name: fact_replenishment_order
      grain: order_line
      primary_key: [OrderID, OrderLine]
      required_columns:
        - { name: OrderDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: SupplierID, type: string, role: supplier_key }
        - { name: "Order Qty", type: decimal, role: quantity }
        - { name: "Forecast Qty", type: decimal, role: quantity }
        - { name: "Safety Stock Qty", type: decimal, role: helper }
        - { name: "Reorder Point Qty", type: decimal, role: helper }
        - { name: "Lead Time Days", type: int, role: helper }
    - name: fact_fulfillment
      grain: delivery_line
      primary_key: [DeliveryID, DeliveryLine]
      required_columns:
        - { name: DeliveryDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Delivered Qty", type: decimal, role: quantity }
        - { name: "Demand Qty", type: decimal, role: quantity }
        - { name: "Stock-Out Flag", type: bool, role: indicator }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
    - name: dim_supplier
      grain: supplier
      primary_key: [SupplierID]
  relationships:
    - { from: fact_replenishment_order.OrderDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.DeliveryDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_fulfillment.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_replenishment_order.SupplierID, to: dim_supplier.SupplierID, cardinality: many-to-one, direction: single }
model_mapping:
  "Order Qty": "fact_replenishment_order[Order Qty]"
  "Delivered Qty": "fact_fulfillment[Delivered Qty]"
  "Demand Qty": "fact_fulfillment[Demand Qty]"
  "Forecast Qty": "fact_replenishment_order[Forecast Qty]"
  "Safety Stock Qty": "fact_replenishment_order[Safety Stock Qty]"
  "Reorder Point Qty": "fact_replenishment_order[Reorder Point Qty]"
  "Lead Time Days": "fact_replenishment_order[Lead Time Days]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Supplier": "dim_supplier[SupplierID]"
---

# Replenishment Optimization & Service Level Management

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
