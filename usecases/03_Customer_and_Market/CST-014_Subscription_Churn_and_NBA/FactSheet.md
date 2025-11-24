---
id: "CST-014"
title: "Subscription Churn & Next-Best-Action"
domain: "Customer and Market"
owner: "Head of Customer Success / Subscription Business"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Churn %", "CLV %"]
supports_strategic_kpi_ids:
  ["crm.churn.pct", "crm.clv.amount"]
action_codes: ["C1", "P2", "M3", "SP1"]
expected_impact: "Reduce churn in subscription models by predicting risk and recommending targeted next-best-actions per subscriber."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Subscription.Plan",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Subscription_Status_Consistent", "Churn_Definition_Documented"]
required_kpi_ids:
  [
    "crm.clv.amount",
    "crm.retention.pct",
    "crm.churn.pct",
  ]
required_kpis:
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
data_requirements:
  facts:
    - name: fact_subscription
      grain: subscription_period
      primary_key: [SubscriptionID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: SubscriptionID, type: string, role: attribute }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Plan", type: string, role: attribute }
        - { name: "MRR Amount", type: decimal, role: amount }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "Churn Flag", type: bool, role: indicator }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "CLV Amount", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LifecycleStage, type: string }
  relationships:
    - { from: fact_subscription.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_subscription.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "MRR Amount": "fact_subscription[MRR Amount]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Customer": "dim_customer[CustomerID]"
  "Date": "dim_date[Date]"
---

# Subscription Churn & Next-Best-Action

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
