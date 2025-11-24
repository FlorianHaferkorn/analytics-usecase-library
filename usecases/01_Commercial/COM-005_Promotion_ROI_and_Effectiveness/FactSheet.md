---
id: "COM-005"
title: "Promotion ROI & Effectiveness"
domain: "Commercial"
owner: "Head of Marketing Controlling / Trade Marketing"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct"]
action_codes: ["D1", "D2", "P2", "M3"]
expected_impact: "+1-2 pp Gross Margin %, +3 % Net Sales in promoted lines"
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
qa_asserts: ["RI_OK", "Baseline_Method_Documented", "Promo_Period_Flag_Consistent"]
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
        - { name: "Promo Flag", type: bool, role: indicator }
        - { name: "Promo ID", type: string, role: attribute }
        - { name: "Promo Type", type: string, role: attribute }
        - { name: "Promo Cost Amount", type: decimal, role: amount }
    - name: fact_marketing_spend
      grain: promo_campaign
      primary_key: [PromoID]
      required_columns:
        - { name: PromoID, type: string, role: attribute }
        - { name: "Planned Promo Cost Amount", type: decimal, role: amount }
        - { name: "Channel", type: string, role: channel }
        - { name: "Start Date", type: date, role: helper }
        - { name: "End Date", type: date, role: helper }
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
    - { from: fact_marketing_spend.PromoID, to: fact_sales.PromoID, cardinality: one-to-many, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Promo Flag": "fact_sales[Promo Flag]"
  "Promo ID": "fact_sales[Promo ID]"
  "Promo Type": "fact_sales[Promo Type]"
  "Promo Cost Amount": "fact_sales[Promo Cost Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Product": "dim_product[ProductID]"
---

# Promotion ROI & Effectiveness

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
