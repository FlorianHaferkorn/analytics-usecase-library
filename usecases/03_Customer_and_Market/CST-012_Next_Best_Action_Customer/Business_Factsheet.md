---
id: "CST-012"
title: "Next-Best-Action Customer (NBA)"
domain: "Customer and Market"
owner: "Head of CRM / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Customer Retention %", "CLV %"]
supports_strategic_kpi_ids: ["crm.retention.pct", "crm.clv.amount"]
action_codes: ["C1", "P2", "M3", "SP1"]
expected_impact: "Increase CLV and retention by recommending the best next action per customer (offer, channel, timing) based on propensity, risk and value."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Customer.Segment",
    "Customer.LifecycleStage",
    "Org.Region>BusinessUnit",
    "Time.Year>Quarter>Month",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["Customer_ID_Consistent", "Consent_Settings_Respected"]
required_kpi_ids:
  [
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.clv.amount",
    "crm.cross_sell_ratio.pct",
    "crm.basket_size.amount",
    "crm.basket_size.units",
    "crm.acquisition.cac.amount",
  ]
required_kpis:
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.cross_sell_ratio.pct: "Cross-Sell Ratio %"
  crm.basket_size.amount: "Average Basket Value"
  crm.basket_size.units: "Average Basket Units"
  crm.acquisition.cac.amount: "Customer Acquisition Cost (CAC) Amount"
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
        - { name: CustomerID, type: string, role: customer_key }
        - { name: ProductID, type: string, role: product_key }
    - name: fact_customer_metrics
      grain: customer_period
      primary_key: [CustomerID, Period]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Active Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_marketing_interactions
      grain: interaction
      primary_key: [InteractionID]
      required_columns:
        - { name: InteractionID, type: string, role: attribute }
        - { name: DateTime, type: datetime, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Channel", type: string, role: channel }
        - { name: "CampaignID", type: string, role: attribute }
        - { name: "Response Flag", type: bool, role: indicator }
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
        - { name: BusinessUnit, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LifecycleStage, type: string }
        - { name: "Consent Marketing Flag", type: bool }
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_marketing_interactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "Units Qty": "fact_sales[Units Qty]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Next-Best-Action Customer (NBA) - Business Factsheet

## 1. Summary
- **Business Goal:** Increase customer lifetime value and retention by recommending the best next action per customer, based on their risk, propensity and value, and by orchestrating actions across channels.

---
- **Target Audience:** Head of CRM / Marketing
- **Business Priority:** High
- **Expected Impact:** Increase CLV and retention by recommending the best next action per customer (offer, channel, timing) based on propensity, risk and value.

## 2. Core Questions
- Welche Kunden sind akut churngefhrdet und sollten mit welcher Manahme angesprochen werden?
- Welche Kunden haben hohe Cross-Sell- oder Upsell-Potenziale?
- Welche Aktionen liefern die beste Kombination aus CLV-Impact und Kosten?
- ber welche Kanle (E-Mail, App, Call-Center, Auendienst) sollten wir welche Aktionen aussteuern?
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
- KPI cards for Customer Retention %, Customer Churn Rate %, Customer Lifetime Value (CLV) Amount, Cross-Sell Ratio %, Average Basket Value with Plan/LY deltas.
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