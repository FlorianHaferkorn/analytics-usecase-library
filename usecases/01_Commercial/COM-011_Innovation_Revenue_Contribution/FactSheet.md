---
id: "COM-011"
title: "Innovation Revenue Contribution"
domain: "Commercial"
owner: "Head of Innovation / Head of Product"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Revenue Growth %", "Innovation Rate %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "people.innovation_rate.pct"]
action_codes: ["I2", "P2", "SP1"]
expected_impact: "Increase revenue share from new products and strengthen portfolio freshness."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "Product.Category>Subcategory>SKU",
  "Lifecycle.Stage",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 24M",
  "Org: All",
  "Lifecycle Stage: All"
]
qa_asserts: ["RI_OK", "LaunchDate_Present", "Lifecycle_Stage_Consistent"]
required_kpi_ids: [
  "people.new_product_share",
  "people.innovation_rate.pct",
  "sales.net_sales.amount",
  "margin.gm.pct"
]
required_kpis:
  people.new_product_share: "New Product Revenue Share %"
  people.innovation_rate.pct: "Innovation Rate %"
  sales.net_sales.amount: "Net Sales Amount"
  margin.gm.pct: "Gross Margin %"
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
        - { name: Channel, type: string, role: channel }
  dims:
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
        - { name: LifecycleStage, type: string }
        - { name: LaunchDate, type: date }
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
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Product": "dim_product[ProductID]"
  "Lifecycle Stage": "dim_product[LifecycleStage]"
  "Launch Date": "dim_product[LaunchDate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# Innovation Revenue Contribution

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
