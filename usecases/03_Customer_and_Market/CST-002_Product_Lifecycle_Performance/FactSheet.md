---
id: "CST-002"
title: "Product Lifecycle Performance"
domain: "Customer and Market"
owner: "Head of Category Management / Product Strategy"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Innovation Revenue %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct", "prod.lifecycle.new_share.pct"]
action_codes: ["D1", "SP1", "P2", "SP2", "M3"]
expected_impact: "-10-20 % SKU count; +2 pp GM %; +3-5 % revenue from new launches"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Lifecycle.Stage",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Lifecycle Stage: All"
]
qa_asserts: ["RI_OK", "LaunchDate_Present", "Phase_Coverage_Complete"]
required_kpi_ids: [
  "prod.lifecycle.new_share.pct",
  "prod.contribution_margin.pct",
  "prod.lifecycle.age.months",
  "prod.roi.pct",
  "prod.lifecycle.phase_distribution.pct"
]
required_kpis:
  prod.lifecycle.new_share.pct: "New Product Share %"
  prod.contribution_margin.pct: "Product Contribution Margin %"
  prod.lifecycle.age.months: "Lifecycle Age (months)"
  prod.roi.pct: "Product ROI %"
  prod.lifecycle.phase_distribution.pct: "Phase Distribution %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Promo Cost Amount", type: decimal, role: amount }
        - { name: Channel, type: string, role: channel }
    - name: fact_product_investment
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: LaunchDate, type: date, role: date_key }
        - { name: DevelopmentCost, type: decimal, role: amount }
        - { name: MarketingCost, type: decimal, role: amount }
        - { name: LifecycleStage, type: string, role: attribute }
  dims:
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
        - { name: Brand, type: string }
        - { name: Status, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_product_investment.ProductID, to: dim_product.ProductID, cardinality: one-to-one, direction: both }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "Promo Cost Amount": "fact_sales[Promo Cost Amount]"
  "Development Cost": "fact_product_investment[DevelopmentCost]"
  "Marketing Cost": "fact_product_investment[MarketingCost]"
  "Launch Date": "fact_product_investment[LaunchDate]"
  "Lifecycle Stage": "fact_product_investment[LifecycleStage]"
  "Product": "dim_product[ProductID]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# Product Lifecycle Performance

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
