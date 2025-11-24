---
id: "{{PREFIX}}-000"
title: "[Insert Use Case Title]"
domain: "[Commercial / Operational Efficiency / Customer & Market / Corporate & Strategy]"
owner: "[Business Owner / Responsible Department]"
impact: "[High / Medium / Low]"
status: "[Draft / Ready / Archived]"
last_update: "DD.MM.YYYY"
reporting_level: "[Strategic / Tactical / Operational]"
analytics_stage: "[Descriptive / Diagnostic / Predictive / Prescriptive]"
maturity: "[Idea / Pilot / Production]"
supports_strategic_kpi: ["Readable KPI Name"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct"]
action_codes: ["P2","D1"]
expected_impact: "[Narrative of expected outcome, e.g., '+2-5 pp ?% Net Sales']"
dataset_model: "[PBIP model name, e.g., Contoso Sales Sample for Power BI Desktop.SemanticModel]"
page_template: "[overview_drivers_details | drivers_details | other registered template]"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week>Day"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK","DeltaPct_PositivePlan"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.delta_pct.ly"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  sales.net_sales.delta_pct.ly: "?% Net Sales"
data_requirements:
  facts:
    - name: fact_main
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel, type: string, role: channel }
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
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_main.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_main.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_main.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_main[Net Sales Amount]"
  "Units Qty": "fact_main[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---
# Use Case Factsheet (Legacy Stub)

Dieses Template dient nur noch als Einstiegspunkt. Bitte erstelle pro Use Case zwei Dateien auf Basis der zentralen Vorlagen:

- [Business_Factsheet_Template.md](./Business_Factsheet_Template.md)
- [Technical_Factsheet_Template.md](./Technical_Factsheet_Template.md)

Das historische FactSheet darf leer bleiben oder wie bei OPS-001/OPS-002 lediglich auf die beiden Dokumente verweisen.
