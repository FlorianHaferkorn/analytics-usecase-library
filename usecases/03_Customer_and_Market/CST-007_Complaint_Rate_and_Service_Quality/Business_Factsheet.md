---
id: "CST-007"
title: "Complaint Rate & Service Quality"
domain: "Customer and Market"
owner: "Head of Customer Service / Customer Experience"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Complaint Rate %", "Customer Retention %"]
supports_strategic_kpi_ids: ["crm.complaint.rate.pct", "crm.retention.pct"]
action_codes: ["C3", "D1", "M3"]
expected_impact: "-0.3 pp complaint rate; improved NPS and retention."
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
  "Channel: All",
  "Segment: All"
]
qa_asserts: ["RI_OK", "Complaints_Mapped_To_Orders", "Complaint_Rate_Within_0_100"]
required_kpi_ids: [
  "crm.complaint.rate.pct",
  "crm.complaint.count",
  "crm.retention.pct"
]
required_kpis:
  crm.complaint.rate.pct: "Complaint Rate %"
  crm.complaint.count: "Complaint Count"
  crm.retention.pct: "Customer Retention %"
data_requirements:
  facts:
    - name: fact_complaints
      grain: complaint
      primary_key: [ComplaintID]
      required_columns:
        - { name: ComplaintID, type: string, role: attribute }
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: "OrderID", type: string, role: attribute }
        - { name: "Complaint Date", type: date, role: date_key }
        - { name: "Category", type: string, role: attribute }
        - { name: "Reason", type: string, role: attribute }
        - { name: "Severity", type: string, role: status }
        - { name: "Status", type: string, role: status }
    - name: fact_customer_transactions
      grain: customer_day
      primary_key: [CustomerID, Date]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Date, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: Channel, type: string, role: channel }
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
    - { from: fact_complaints.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_complaints."Complaint Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_transactions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_transactions.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Complaint ID": "fact_complaints[ComplaintID]"
  "Complaint Date": "fact_complaints[Complaint Date]"
  "Complaint Reason": "fact_complaints[Reason]"
  "Complaint Severity": "fact_complaints[Severity]"
  "Complaint Status": "fact_complaints[Status]"
  "Customer ID": "dim_customer[CustomerID]"
  "Channel": "fact_customer_transactions[Channel]"
  "Date": "dim_date[Date]"
---

# Complaint Rate & Service Quality - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and reduce complaint rates across segments, channels, and products, and improve service quality by focusing on root causes of complaints.

---
- **Target Audience:** Head of Customer Service / Customer Experience
- **Business Priority:** High
- **Expected Impact:** -0.3 pp complaint rate; improved NPS and retention.

## 2. Core Questions
- What is our complaint rate overall and by region, segment, channel, and product category?
- Which complaint reasons and severities are most frequent?
- How do complaint rates correlate with retention, churn, and NPS?
- Where do process or product changes reduce complaint volume most effectively?
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
- KPI cards for Complaint Rate %, Complaint Count, Customer Retention % with Plan/LY deltas.
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