---
id: "COR-013"
title: "Customer Profitability Across Lifecycle"
domain: "Corporate and Strategy"
owner: "CCO / CFO"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Gross Margin %", "CLV %", "Customer Retention %"]
supports_strategic_kpi_ids:
  ["margin.gm.pct", "crm.clv.amount", "crm.retention.pct"]
action_codes: ["P2", "M3", "C1", "SP1"]
expected_impact: "Understand and manage profitability of customers across their lifecycle, from acquisition to churn, enabling targeted investments and de-investments."
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
    "sales.net_sales.amount",
    "margin.customer.amount",
    "margin.customer.pct",
    "crm.clv.amount",
    "crm.acquisition.cac.amount",
    "crm.retention.pct",
    "crm.churn.pct",
    "crm.complaint.rate.pct",
  ]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  margin.customer.amount: "Customer Margin Amount"
  margin.customer.pct: "Customer Margin %"
  crm.clv.amount: "Customer Lifetime Value (CLV) Amount"
  crm.acquisition.cac.amount: "Customer Acquisition Cost (CAC) Amount"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Customer Churn Rate %"
  crm.complaint.rate.pct: "Complaint Rate %"
data_requirements:
  facts:
    - name: fact_sales
      grain: invoice_line
      primary_key: [InvoiceLineID]
      required_columns:
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
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
        - { name: "Churn Flag", type: bool, role: indicator }
        - { name: "CLV Amount", type: decimal, role: amount }
    - name: fact_marketing_spend
      grain: customer_campaign
      primary_key: [CustomerID, CampaignID]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Acquisition Spend Amount", type: decimal, role: amount }
    - name: fact_complaint
      grain: complaint
      primary_key: [ComplaintID]
      required_columns:
        - { name: ComplaintID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Complaint Cost Amount", type: decimal, role: amount }
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
  relationships:
    - { from: fact_sales.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_metrics.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_marketing_spend.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_complaint.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_complaint.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Net Sales Amount": "fact_sales[Net Sales Amount]"
  "COGS Amount": "fact_sales[COGS Amount]"
  "CLV Amount": "fact_customer_metrics[CLV Amount]"
  "Acquisition Spend Amount": "fact_marketing_spend[Acquisition Spend Amount]"
  "Complaint Cost Amount": "fact_complaint[Complaint Cost Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Customer Profitability Across Lifecycle - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and manage customer profitability over the entire lifecycle " from acquisition to retention and churn " in order to reallocate spend towards high-value segments and reduce investments in unprofitable relationships.

---
- **Target Audience:** CCO / CFO
- **Business Priority:** High
- **Expected Impact:** Understand and manage profitability of customers across their lifecycle, from acquisition to churn, enabling targeted investments and de-investments.

## 2. Core Questions
- Welche Kundensegmente liefern ber ihren Lifecycle die hchste und niedrigste Profitabilitt?
- Wie verhalten sich CAC und CLV nach Kanal, Segment und Kampagne?
- Welche Muster erkennen wir bei Churn, Complaints und Rckgabe-/Servicekosten?
- Wo investieren wir heute zu viel Akquisitionsbudget fr Kunden mit schwacher Margen- oder Wiederkaufs-Performance?
- Welche konkreten Manahmen zur Verbesserung von CLV (Cross-Sell, Retention, Servicequalitt) sind am wirkungsvollsten?
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
- KPI cards for Net Sales Amount, Customer Margin Amount, Customer Margin %, Customer Lifetime Value (CLV) Amount, Customer Acquisition Cost (CAC) Amount with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a