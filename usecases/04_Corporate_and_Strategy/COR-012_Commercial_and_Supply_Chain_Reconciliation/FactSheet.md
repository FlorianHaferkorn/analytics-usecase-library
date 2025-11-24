---
id: "COR-012"
title: "Commercial & Supply Chain Reconciliation"
domain: "Corporate and Strategy"
owner: "COO / Head of Commercial & Supply Chain"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "CCC Days"]
supports_strategic_kpi_ids:
  ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days"]
action_codes: ["P2", "W1", "D1", "SP1"]
expected_impact: "Avoid siloed commercial and operations decisions by reconciling promotions, pricing and forecast changes with stock, capacity and working capital."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
    "Product.Category>Subcategory",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts:
  [
    "Promo_Flag_Consistent",
    "Forecast_Version_Frozen",
    "Inventory_Valuation_Reconciles",
  ]
required_kpi_ids:
  [
    "sales.net_sales.amount",
    "sales.promo.roi.pct",
    "sales.promo.uplift_pct",
    "margin.promo.incremental.amount",
    "ops.stockout.pct",
    "ops.inventory.days",
    "ops.inventory.turnover",
    "ops.working_capital.ccc.days",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  margin.promo.incremental.amount: "Incremental GM Amount"
  ops.stockout.pct: "Stockout Rate %"
  ops.inventory.days: "Inventory Days on Hand (DIO)"
  ops.inventory.turnover: "Inventory Turnover"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
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
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
    - name: fact_inventory
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Inventory Amount", type: decimal, role: amount }
        - { name: "Inventory Units Qty", type: decimal, role: quantity }
    - name: fact_service_level
      grain: org_product_period
      primary_key: [OrgID, ProductID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Order Lines Total", type: int, role: quantity }
        - { name: "Order Lines Stockout", type: int, role: quantity }
    - name: fact_working_capital
      grain: org_period_wc
      primary_key: [OrgID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "DSO Days", type: decimal, role: helper }
        - { name: "DPO Days", type: decimal, role: helper }
        - { name: "DIO Days", type: decimal, role: helper }
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
        - { name: BusinessUnit, type: string }
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
    - { from: fact_service_level.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_service_level.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_working_capital.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Promo ID": "fact_sales[Promo ID]"
  "Inventory Amount": "fact_inventory[Inventory Amount]"
  "Inventory Units Qty": "fact_inventory[Inventory Units Qty]"
  "Order Lines Total": "fact_service_level[Order Lines Total]"
  "Order Lines Stockout": "fact_service_level[Order Lines Stockout]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Commercial & Supply Chain Reconciliation

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
