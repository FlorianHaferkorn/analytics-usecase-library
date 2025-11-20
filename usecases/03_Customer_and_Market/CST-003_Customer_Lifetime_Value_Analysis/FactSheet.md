---
id: "CST-003"
title: "Customer Lifetime Value Analysis"
domain: "Customer & Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Predictive"
supports_strategic_kpi: ["Customer Lifetime Value", "Customer Retention %", "Gross Margin %"]
supports_strategic_kpi_ids: ["crm.clv.amount", "crm.retention.pct", "margin.gm.pct"]
action_codes: ["D1", "M3"]
expected_impact: "+2 % CLV and +1 pp Gross Margin % by focusing on high-value customers and improving retention."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Customer Group>Customer",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "CLV_Model_Documented", "CLV_Reconciles_to_Margin"]
required_kpi_ids: [
  "crm.clv.amount",
  "crm.retention.pct",
  "crm.churn.pct",
  "crm.reactivation.pct",
  "crm.at_risk_share.pct",
  "crm.active_customers_start.count",
  "crm.active_customers_end.count",
  "crm.churned_customers.count",
  "crm.reactivated_customers.count",
  "crm.at_risk_customers.count",
  "crm.active_customers.count"
]
required_kpis:
  crm.clv.amount: "CLV (Customer Lifetime Value)"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Churn %"
  crm.reactivation.pct: "Reactivation Rate %"
  crm.at_risk_share.pct: "At-Risk Share %"
  crm.active_customers_start.count: "Active Customers Start"
  crm.active_customers_end.count: "Active Customers End"
  crm.churned_customers.count: "Lost Customers Count"
  crm.reactivated_customers.count: "Reactivated Customers Count"
  crm.at_risk_customers.count: "At-Risk Customers Count"
  crm.active_customers.count: "Active Customers"
data_requirements:
  facts:
    - name: fact_customer_transactions
      grain: customer_period
      primary_key: [CustomerID, PeriodKey]
      required_columns:
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: "PeriodKey", type: string, role: period_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Margin Amount", type: decimal, role: amount }
        - { name: "Status", type: string, role: attribute }
        - { name: "At-Risk Flag", type: bool, role: indicator }
        - { name: "Reactivated Flag", type: bool, role: indicator }
    - name: fact_customer_clv
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: "CLV Amount", type: decimal, role: amount }
  dims:
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: CustomerGroup, type: string }
        - { name: CustomerName, type: string }
        - { name: ChannelDefault, type: string }
    - name: dim_period
      grain: period
      primary_key: [PeriodKey]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: string }
        - { name: Month, type: int }
  relationships:
    - { from: fact_customer_transactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_transactions.PeriodKey, to: dim_period.PeriodKey, cardinality: many-to-one, direction: single }
    - { from: fact_customer_clv.CustomerID, to: dim_customer.CustomerID, cardinality: one-to-one, direction: single }
model_mapping:
  "Margin Amount": "fact_customer_transactions[Margin Amount]"
  "Net Sales Amount": "fact_customer_transactions[Net Sales Amount]"
  "COGS Amount": "fact_customer_transactions[COGS Amount]"
  "Customer": "dim_customer[CustomerID]"
  "Period": "dim_period[PeriodKey]"
---

# Use Case Fact Sheet

## 1. Business Goal
Quantify and compare the long-term economic value of customers and segments to focus acquisition, retention, and service investments on those that drive the highest contribution to margin.

## 2. Business Questions
- What is the current distribution of CLV across customers, segments, and regions?
- Which customers combine high CLV with strong recent margin contribution, and which are at risk?
- How do retention, churn, and reactivation dynamics impact CLV over time?
- Which levers (pricing, mix, engagement) can increase CLV for specific segments?

## 3. Scope & Assumptions
- CLV is defined as discounted gross margin over a defined time horizon per customer.
- Only customers with sufficient transaction history are included in CLV calculation.
- Status flags (active, lost, reactivated, at-risk) are derived from transaction patterns and scoring models.

## 4. Target Users & Decisions
- Target users: CRM teams, Marketing Analytics, Sales and Customer Success.
- Decisions:
  - Prioritize retention and upsell activities for high-CLV customers.
  - Identify low-CLV or negative-margin customers for repricing or service adjustment.
  - Design campaigns to increase lifetime value in target segments.

## 5. KPIs & Drivers (Overview)
- Strategic KPIs:
  - Customer Lifetime Value (CLV)
  - Customer Retention %
  - Churn %, Reactivation Rate %, At-Risk Share %
- Analytical drivers:
  - Active customers (start/end), churned and reactivated customers.
  - Margin Amount and Net Sales Amount by customer and segment.

## 6. Required KPIs (Detail)
See `required_kpi_ids` and `required_kpis` in the front matter for the exact KPI IDs and labels used for implementation.

## 7. Data & Modelling Notes
- CLV model assumptions (discount rate, horizon, churn model) must be documented and versioned.
- Customer and period keys must be stable and consistent across facts and dimensions.
- Margin allocation to customers must reconcile to overall gross margin within tolerance thresholds.

## 8. Page Layout / Storyboard
- Overview: CLV distribution by customer segment and region, with top/bottom lists.
- Drivers: Retention/churn/reactivation views to explain CLV differences.
- Actions: Segment-level recommendations for campaigns and account management.
