---
id: "COM-003"
title: "Promotion Effectiveness (ROI & Uplift)"
domain: "Commercial"
owner: "Head of Marketing Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "Revenue Growth %"]
supports_strategic_kpi_ids: ["margin.gm.pct", "sales.revenue.growth_pct"]
action_codes: ["D1", "P2", "D2", "O2", "SP1"]
expected_impact: "+10-30 % ROI uplift; +0.5-1.0 pp GM %; +1-3 pp Δ% NS"

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
  "sales.promo.roi.pct",
  "sales.promo.uplift_pct",
  "sales.promo.incremental.amount",
  "margin.promo.incremental.amount",
  "margin.promo.gm.pct",
  "sales.promo.cost.amount"
]
required_kpis:
  sales.promo.roi.pct: "Promo ROI %"
  sales.promo.uplift_pct: "Promo Uplift %"
  sales.promo.incremental.amount: "Incremental Sales Amount"
  margin.promo.incremental.amount: "Incremental GM Amount"
  margin.promo.gm.pct: "GM % During Promo"
  sales.promo.cost.amount: "Promo Cost Amount"
---

# Promotion Effectiveness (ROI & Uplift)

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
