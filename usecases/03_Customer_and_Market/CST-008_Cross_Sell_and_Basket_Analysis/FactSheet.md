---
id: "CST-008"
title: "Cross-Sell & Basket Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Category Management"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Cross-Sell Ratio %", "Customer Lifetime Value"]
supports_strategic_kpi_ids: ["crm.cross_sell_ratio.pct", "crm.clv.amount"]
action_codes: ["C2", "M3", "P2"]
expected_impact: "+5–10 % basket size and cross-sell ratio in target segments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Region>Market",
  "Customer.Segment>LoyaltyTier",
  "Channel",
  "Product.Category>Subcategory",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Customer_Key_Unique", "Basket_Size_InRange"]
required_kpi_ids: [
  "crm.cross_sell_ratio.pct",
  "crm.basket_size.amount",
  "crm.basket_size.units"
]
required_kpis:
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
data_requirements:
  facts:
    - name: fact_sales
      grain: transaction_line
      primary_key: [TransactionID, LineID]
      required_columns:
        - { name: TransactionID, type: string, role: attribute }
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Channel, type: string, role: channel }
        - { name: Category, type: string, role: attribute }
        - { name: Subcategory, type: string, role: attribute }
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
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Transaction ID": "fact_sales[TransactionID]"
  "Customer ID": "dim_customer[CustomerID]"
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "Category": "fact_sales[Category]"
  "Subcategory": "fact_sales[Subcategory]"
  "Channel": "fact_sales[Channel]"
  "Date": "dim_date[Date]"
---

# Cross-Sell & Basket Analysis

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
