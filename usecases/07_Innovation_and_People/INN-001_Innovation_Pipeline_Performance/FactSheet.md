---
id: "INN-001"
title: "Innovation Pipeline Performance"
domain: "Innovation & People"
owner: "Head of Strategy & Innovation"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Innovation Rate %", "New Product Revenue %"]
supports_strategic_kpi_ids: ["people.new_product_share"]
action_codes: ["I2"]
expected_impact: "+1 pp Innovation Rate durch besseres Pipeline-Management und Priorisierung."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Portfolio.Pillar>Program>Project",
  "Product.Category>Subcategory>SKU",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 24M",
  "Status: All"
]
qa_asserts: ["RI_OK", "Idea_Stages_Consistent"]
required_kpi_ids: [
  "people.new_product_share"
]
required_kpis:
  people.new_product_share: "New Product Share %"
data_requirements:
  facts:
    - name: fact_innovation
      grain: idea
      primary_key: [IdeaID]
      required_columns:
        - { name: IdeaID, type: string, role: attribute }
        - { name: Stage, type: string, role: attribute }
        - { name: CreatedDate, type: date, role: date_key }
        - { name: ImplementedFlag, type: bool, role: indicator }
    - name: fact_sales
      grain: product_month
      primary_key: [ProductID, Month]
      required_columns:
        - { name: ProductID, type: string, role: product_key }
        - { name: Month, type: date, role: date_key }
        - { name: NetSalesAmount, type: decimal, role: amount }
        - { name: IsNewProduct, type: bool, role: indicator }
  dims:
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
model_mapping:
  "Idea ID": "fact_innovation[IdeaID]"
  "Idea Stage": "fact_innovation[Stage]"
  "Product ID": "fact_sales[ProductID]"
  "Net Sales Amount": "fact_sales[NetSalesAmount]"
---

# Innovation Pipeline Performance

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
