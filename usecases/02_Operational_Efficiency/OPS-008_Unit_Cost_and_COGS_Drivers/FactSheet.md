---
id: "OPS-008"
title: "Unit Cost & COGS Drivers"
domain: "Operational Efficiency"
owner: "Head of Operations / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "COGS % of Sales"]
supports_strategic_kpi_ids: ["margin.gm.pct", "cost.cogs.amount"]
action_codes: ["PC2", "M1", "O2"]
expected_impact: "-2–4 % unit cost; +0.5–1.0 pp gross margin %."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Plant>Line",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All"
]
qa_asserts: ["RI_OK", "COGS_Positive", "UnitCost_Reconciles"]
required_kpi_ids: [
  "cost.cogs.amount",
  "ops.process.cost_per_unit.amount"
]
required_kpis:
  cost.cogs.amount: "COGS Amount"
  ops.process.cost_per_unit.amount: "Process Cost per Unit"
data_requirements:
  facts:
    - name: fact_production
      grain: product_line_day
      primary_key: [ProductionID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Direct Labor Cost Amount", type: decimal, role: amount }
        - { name: "Energy Cost Amount", type: decimal, role: amount }
        - { name: "Material Cost Amount", type: decimal, role: amount }
        - { name: "Other Production Cost Amount", type: decimal, role: amount }
    - name: fact_cogs
      grain: product_org_period
      primary_key: [CogsID]
      required_columns:
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Plant, type: string }
        - { name: Line, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_production.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_production.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_production.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_cogs.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Direct Labor Cost Amount": "fact_production[Direct Labor Cost Amount]"
  "Energy Cost Amount": "fact_production[Energy Cost Amount]"
  "Material Cost Amount": "fact_production[Material Cost Amount]"
  "Other Production Cost Amount": "fact_production[Other Production Cost Amount]"
  "COGS Amount": "fact_cogs[COGS Amount]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
---

# Unit Cost & COGS Drivers

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
