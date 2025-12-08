---
id: "CST-001"
title: "Customer Retention & Churn Analysis"
domain: "Customer and Market"
owner: "Head of CRM / Marketing Analytics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Customer Retention %", "CLV %", "Revenue Growth %"]
supports_strategic_kpi_ids: ["crm.retention.pct", "crm.clv.amount", "sales.revenue.growth_pct"]
action_codes: ["C1", "C2", "D1", "SP1", "O2"]
expected_impact: "+3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Region>Market>Store",
  "Customer.Segment>LoyaltyTier",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Customer Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Retention_Range", "Customer_Key_Unique"]
required_kpi_ids: [
  "crm.retention.pct",
  "crm.churn.pct",
  "crm.clv.amount",
  "crm.reactivation.pct",
  "crm.at_risk_share.pct"
]
required_kpis:
  crm.retention.pct: "Retention %"
  crm.churn.pct: "Churn %"
  crm.clv.amount: "CLV (Customer Lifetime Value)"
  crm.reactivation.pct: "Reactivation Rate %"
  crm.at_risk_share.pct: "At-Risk Share %"
data_requirements:
  facts:
    - name: fact_customer_transactions
      grain: customer_day
      primary_key: [CustomerID, Date]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Margin Amount", type: decimal, role: amount }
        - { name: "Units Qty", type: int, role: quantity }
        - { name: Channel, type: string, role: channel }
    - name: fact_customer_profile
      grain: customer_month
      primary_key: [CustomerID, SnapshotMonth]
      required_columns:
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: Segment, type: string, role: segment }
        - { name: LoyaltyTier, type: string, role: attribute }
        - { name: "Last Purchase Date", type: date, role: helper }
        - { name: "Visit Frequency", type: decimal, role: helper }
        - { name: "Basket Size", type: decimal, role: helper }
        - { name: "Churn Flag", type: bool, role: indicator }
  dims:
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Region, type: string }
        - { name: Market, type: string }
        - { name: AcquisitionChannel, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_customer_transactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_transactions.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profile.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_profile.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Customer ID": "dim_customer[CustomerID]"
  "Region": "dim_customer[Region]"
  "Market": "dim_customer[Market]"
  "Net Sales Amount": "fact_customer_transactions[Net Sales Amount]"
  "Margin Amount": "fact_customer_transactions[Margin Amount]"
  "Last Purchase Date": "fact_customer_profile[Last Purchase Date]"
  "Visit Frequency": "fact_customer_profile[Visit Frequency]"
  "Basket Size": "fact_customer_profile[Basket Size]"
  "Churn Flag": "fact_customer_profile[Churn Flag]"
  "Date": "dim_date[Date]"
---

# Customer Retention & Churn Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** Increase customer lifetime value by identifying churn risks early, improving retention strategies, and quantifying the business impact of lost customers.

---
- **Target Audience:** Head of CRM / Marketing Analytics
- **Business Priority:** High
- **Expected Impact:** +3-5 pp Retention; +5-10 % incremental margin; +15-25 % ROI on retention campaigns

## 2. Core Questions
- What is the current retention and churn rate?
- Which segments show the highest churn risk?
- What behaviors precede churn (e.g., declining frequency, basket size)?
- Which actions or offers most effectively prevent churn?
- How much incremental margin is gained per retained customer?
---

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
- KPI cards for Retention %, Churn %, CLV (Customer Lifetime Value), Reactivation Rate %, At-Risk Share % with Plan/LY deltas.
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