---
id: "CST-013"
title: "CLV & Retention Drivers"
domain: "Customer and Market"
owner: "Head of CRM / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["CLV %", "Customer Retention %"]
supports_strategic_kpi_ids:
  ["crm.clv.amount", "crm.retention.pct"]
action_codes: ["C1", "P2", "M3"]
expected_impact: "Understand the drivers of CLV and retention across segments and behaviors to focus marketing and service spend on the most effective levers."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 24M", "Org: All"]
qa_asserts: ["Customer_ID_Consistent", "Lifecycle_Stage_Defined"]
required_kpi_ids:
  [
    "crm.clv.amount",
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.basket_size.amount",
    "crm.basket_size.units",
    "crm.cross_sell_ratio.pct",
  ]
required_kpis:
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
data_requirements:
  facts:
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "CLV Amount", type: decimal, role: amount }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Date, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LifecycleStage, type: string }
  relationships:
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Customer": "dim_customer[CustomerID]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---

# CLV & Retention Drivers

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
