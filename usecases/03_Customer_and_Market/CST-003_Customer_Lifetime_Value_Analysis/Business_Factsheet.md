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

# Customer Lifetime Value Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** Quantify and compare the long-term economic value of customers and segments to focus acquisition, retention, and service investments on those that drive the highest contribution to margin.
- **Target Audience:** Head of CRM / Marketing Analytics
- **Business Priority:** High
- **Expected Impact:** +2 % CLV and +1 pp Gross Margin % by focusing on high-value customers and improving retention.

## 2. Core Questions
- n/a

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for CLV (Customer Lifetime Value), Customer Retention %, Churn %, Reactivation Rate %, At-Risk Share % with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a