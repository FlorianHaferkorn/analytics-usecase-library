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

# Complaint Rate & Service Quality

## 1. Business Goal
Measure and reduce complaint rates across segments, channels, and products, and improve service quality by focusing on root causes of complaints.

---

## 2. Business Context
Complaints are a leading indicator of customer dissatisfaction and churn risk.  
However, complaints are often tracked in separate systems (call center, ticketing) and not consistently linked to customers, orders, or products.  
This Use Case connects complaint data with transactional and customer data to create actionable views.

---

## 3. Key Questions
- What is our complaint rate overall and by region, segment, channel, and product category?
- Which complaint reasons and severities are most frequent?
- How do complaint rates correlate with retention, churn, and NPS?
- Where do process or product changes reduce complaint volume most effectively?

---

## 4. Key KPIs
| KPI               | Definition                                 | Unit | Format    |
|-------------------|--------------------------------------------|------|-----------|
| Complaint Rate %  | Complaints / Transactions or Customers     | %    | 1 decimal |
| Complaint Count   | Number of complaints                       | #    | 0 decimals|
| Customer Retention % | Customers retained vs baseline         | %    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Complaint ID, Date, Reason, Severity, Status
- Customer ID, Segment, Region
- Channel, Product Category (optional via OrderID join)

---

## 6. Segmentation & Hierarchies
- Customer: Region > Market > Segment > LoyaltyTier  
- Channel: Channel Group > Channel  
- Product: Category > Subcategory (via order)  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Definition of a complaint is consistent across channels and systems.
- Only closed, validated complaints are included in the main rate; open ones may be monitored separately.

---

## 8. Data Freshness & Cadence
- Complaints: daily refresh.
- Transactions: daily or weekly.
- Reporting cadence: weekly operational review and monthly service quality review.

---

## 9. Edge Cases & QA Rules
- Complaints without a customer or date are flagged for data quality remediation.
- Complaint rate must be calculated with clearly defined denominator (transactions, customers, or both).

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Complaint fact with IDs, reasons, severity, customer and date.
  - Transaction fact with customer and channel.

---

## 11. Typical Actions
| Action                                  | Code | Expected Effect                    |
|-----------------------------------------|------|------------------------------------|
| Address root causes of frequent complaints | C3 | Complaint rate reduced             |
| Improve service processes in hot spots  | D1   | Faster resolution, fewer repeats   |
| Target retention campaigns at affected customers | M3 | Higher retention, better NPS       |

---

## 12. Expected Business Impact
| Dimension | Expected Impact         | Measurement   |
|-----------|-------------------------|---------------|
| Quality   | -0.3 pp complaint rate | vs prior year |
| Retention | +1–2 pp retention      | vs prior year |

---

## 13. Related Processes
Customer Service Operations → Complaint Handling → Root Cause Analysis → Continuous Improvement.

---

## 14. Insights & Learnings
Typical findings include recurring issues in specific channels, products, or regions that can be fixed with process or product changes.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn Analysis](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-005 NPS Analysis](../CST-005_NPS_Analysis/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

