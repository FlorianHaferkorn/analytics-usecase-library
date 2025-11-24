---
id: "COM-004"
title: "Price-Volume-Mix Bridge (Δ Net Sales & Δ Gross Margin)"
domain: "Commercial"
owner: "Head of Sales Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["P2", "M3", "D1", "SP1", "O2"]
expected_impact: "100% reconciled variance; +0.5-1.5 pp GM %; +1-2 pp Δ% Net Sales"

dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: ["Product.Category>Subcategory>SKU","Org.Region>Area>Store","Channel","Time.Year>Month>Week"]
filters_default: ["Time: Last 12M","Org: All","Channel: All"]
qa_asserts: ["RI_OK"]

data_requirements:
  facts:
    - name: fact_sales
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
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_product
      grain: product
      primary_key: [ProductID]
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.ProductID, to: dim_product.ProductID, cardinality: many-to-one, direction: single }

model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
required_kpi_ids: [
  "sales.net_sales.delta_amount.ly",
  "margin.gm.delta_amount",
  "sales.pvm.price_effect.amount",
  "sales.pvm.volume_effect.amount",
  "sales.pvm.mix_effect.amount",
  "margin.gm.pct"
]
required_kpis:
  sales.net_sales.delta_amount.ly: "Δ Net Sales Amount"
  margin.gm.delta_amount: "Δ Gross Margin Amount"
  sales.pvm.price_effect.amount: "Price Effect Amount"
  sales.pvm.volume_effect.amount: "Volume Effect Amount"
  sales.pvm.mix_effect.amount: "Mix Effect Amount"
  margin.gm.pct: "Gross Margin %"
---

# Price-Volume-Mix Bridge (Δ Net Sales & Δ Gross Margin)

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
