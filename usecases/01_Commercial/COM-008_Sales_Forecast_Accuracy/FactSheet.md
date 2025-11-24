---
id: "COM-008"
title: "Sales Forecast Accuracy"
domain: "Commercial"
owner: "Head of Sales Planning / Demand Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Working Capital %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "ops.working_capital.pct"]
action_codes: ["P2", "I1", "SP1"]
expected_impact: "+5–10 pp forecast accuracy; lower safety stocks and firefighting."
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
qa_asserts: ["RI_OK", "Forecast_vs_Actual_Aligned", "MAPE_InRange"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "sales.net_sales.amount.forecast",
  "sales.forecast.mape_pct",
  "sales.forecast.bias_pct"
]
required_kpis:
  sales.net_sales.amount: "Actual Net Sales Amount"
  sales.net_sales.amount.forecast: "Forecast Net Sales Amount"
  sales.forecast.mape_pct: "Forecast Accuracy (MAPE %)"
  sales.forecast.bias_pct: "Forecast Bias %"
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
    - name: fact_forecast
      grain: sku_period_org
      primary_key: [ForecastID]
      required_columns:
        - { name: "Forecast Net Sales Amount", type: decimal, role: amount }
        - { name: "Forecast Units Qty", type: decimal, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: ProductID, type: string, role: product_key }
        - { name: Channel", type: string, role: channel }
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
        - { name: Area, type: string }
        - { name: Store, type: string }
    - name: dim_product
      grain: product
      primary_key: [ProductID]
      required_columns:
        - { name: Category, type: string }
        - { name: Subcategory, type: string }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.5%" }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_forecast.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Forecast Net Sales Amount": "fact_forecast[Forecast Net Sales Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Sales Forecast Accuracy

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
