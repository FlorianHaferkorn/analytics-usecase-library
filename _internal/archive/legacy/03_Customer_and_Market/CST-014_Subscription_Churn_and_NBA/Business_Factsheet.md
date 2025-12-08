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

# Subscription Churn & Next-Best-Action - Business Factsheet

## 1. Summary
- **Business Goal:** Reduce subscription churn and increase CLV by predicting churn risk and recommending tailored next-best-actions per subscriber.

---
- **Target Audience:** Head of Customer Success / Subscription Business
- **Business Priority:** Very High
- **Expected Impact:** Reduce churn in subscription models by predicting risk and recommending targeted next-best-actions per subscriber.

## 2. Core Questions
- Welche Abonnenten sind akut churngefhrdet und welchen Wert (CLV) reprsentieren sie?
- Welche Manahmen (Preis, Planwechsel, Service-Intervention, Zusatzleistungen) sind pro Segment am wirksamsten?
- Wie verndern sich Churn und CLV nach Umsetzung von NBA-Strategien?
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
- KPI cards for Customer Lifetime Value (CLV) Amount, Customer Retention %, Customer Churn Rate % with Plan/LY deltas.
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