---
id: "CST-011"
title: "Segment Profitability"
domain: "Customer and Market"
owner: "Head of Controlling / Head of Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "Customer Lifetime Value"]
supports_strategic_kpi_ids: ["margin.gm.pct", "crm.clv.amount"]
action_codes: ["P2", "M3", "D1"]
expected_impact: "Shift focus and investment to the most profitable segments and de-prioritize value-destroying segments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Segment>LoyaltyTier",
  "Customer.Region>Market",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Segment_Assignment_Complete", "Margin_Within_Range"]
required_kpi_ids: [
  "margin.customer.amount",
  "margin.customer.pct",
  "crm.clv.amount",
  "crm.retention.pct"
]
required_kpis:
  margin.customer.amount: "Customer Segment Margin Amount"
  margin.customer.pct: "Customer Segment Margin %"
  crm.clv.amount: "Customer Lifetime Value (CLV)"
  crm.retention.pct: "Customer Retention %"
data_requirements:
  facts:
    - name: fact_customer_profitability
      grain: customer_period
      primary_key: [CustomerID, Date]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Service Cost Amount", type: decimal, role: amount }
        - { name: "Marketing Cost Amount", type: decimal, role: amount }
  dims:
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Region, type: string }
        - { name: Market, type: string }
        - { name: Segment, type: string }
        - { name: LoyaltyTier, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_customer_profitability.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profitability.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_customer_profitability[Net Sales Amount]"
  "COGS Amount": "fact_customer_profitability[COGS Amount]"
  "Service Cost Amount": "fact_customer_profitability[Service Cost Amount]"
  "Marketing Cost Amount": "fact_customer_profitability[Marketing Cost Amount]"
  "Customer ID": "dim_customer[CustomerID]"
  "Segment": "dim_customer[Segment]"
  "Date": "dim_date[Date]"
---

# Segment Profitability

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
