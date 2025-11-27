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

# CLV & Retention Drivers - Business Factsheet

## 1. Summary
- **Business Goal:** Explain differences in CLV and retention across segments and behaviors to focus acquisition, pricing and service levers on the most profitable customers.

---
- **Target Audience:** Head of CRM / Marketing
- **Business Priority:** High
- **Expected Impact:** Understand the drivers of CLV and retention across segments and behaviors to focus marketing and service spend on the most effective levers.

## 2. Core Questions
- Welche Segmente liefern den hchsten und niedrigsten CLV und wie entwickeln sich Retention und Churn?
- Welche Verhaltensmuster (Kaufhufigkeit, Warenkorbgre, Cross-Sell) unterscheiden wertvolle von wenig profitablen Kunden?
- Welche Manahmen (z.B. Pricing, Bundles, Loyalty-Programme) korrelieren mit hherem CLV und Retention?
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
- KPI cards for Customer Lifetime Value (CLV) Amount, Customer Retention %, Customer Churn Rate %, Average Basket Value, Average Basket Units with Plan/LY deltas.
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