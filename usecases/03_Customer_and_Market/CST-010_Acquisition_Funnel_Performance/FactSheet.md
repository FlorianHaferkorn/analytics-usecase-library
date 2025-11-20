---
id: "CST-010"
title: "Acquisition Funnel Performance"
domain: "Customer and Market"
owner: "Head of Marketing / Growth Lead"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "New Customer Count"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "crm.new_customers.count"]
action_codes: ["C1", "D2", "P2"]
expected_impact: "Higher conversion along the acquisition funnel; lower cost per acquired customer."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Channel",
  "Campaign.Type>Campaign",
  "Customer.Segment",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Channel: All",
  "Campaign: All"
]
qa_asserts: ["RI_OK", "Funnel_Steps_Consistent", "Attribution_Method_Documented"]
required_kpi_ids: [
  "crm.acquisition.leads.count",
  "crm.acquisition.conversions.count",
  "crm.acquisition.conversion_rate.pct",
  "crm.acquisition.cac.amount"
]
required_kpis:
  crm.acquisition.leads.count: "Leads Count"
  crm.acquisition.conversions.count: "New Customers Acquired"
  crm.acquisition.conversion_rate.pct: "Conversion Rate %"
  crm.acquisition.cac.amount: "Customer Acquisition Cost (CAC)"
data_requirements:
  facts:
    - name: fact_leads
      grain: lead
      primary_key: [LeadID]
      required_columns:
        - { name: LeadID, type: string, role: attribute }
        - { name: "Lead Source", type: string, role: attribute }
        - { name: "Channel", type: string, role: channel }
        - { name: "Campaign", type: string, role: attribute }
        - { name: "Lead Date", type: date, role: date_key }
        - { name: "Lead Status", type: string, role: status }
    - name: fact_acquisitions
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Acquisition Date", type: date, role: date_key }
        - { name: "Channel", type: string, role: channel }
        - { name: "Campaign", type: string, role: attribute }
        - { name: "Acquisition Cost Amount", type: decimal, role: amount }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
  relationships:
    - { from: fact_acquisitions.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_acquisitions."Acquisition Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Lead ID": "fact_leads[LeadID]"
  "Lead Source": "fact_leads[Lead Source]"
  "Lead Status": "fact_leads[Lead Status]"
  "Campaign": "fact_leads[Campaign]"
  "Acquisition Cost Amount": "fact_acquisitions[Acquisition Cost Amount]"
  "Customer ID": "dim_customer[CustomerID]"
  "Date": "dim_date[Date]"
---

# Acquisition Funnel Performance

## 1. Business Goal
Measure and optimize the performance of the acquisition funnel from lead to new customer across channels and campaigns.

---

## 2. Business Context
Marketing and sales often track leads, clicks, and impressions, but lack a consolidated view from first touch to acquired customer and revenue.  
This Use Case provides a structured funnel view with conversion rates and acquisition cost per channel and campaign.

---

## 3. Key Questions
- How many leads and new customers do we generate per channel and campaign?
- What are the conversion rates from lead to customer across funnel stages?
- What is the cost per acquired customer (CAC) by channel and campaign?
- Which campaigns and channels provide the best ROI?

---

## 4. Key KPIs
| KPI                   | Definition                                  | Unit | Format   |
|-----------------------|---------------------------------------------|------|----------|
| Leads Count           | Number of leads created                     | #    | 0 decimals|
| New Customers Acquired| Number of new customers                     | #    | 0 decimals|
| Conversion Rate %     | New Customers / Leads                       | %    | 1 decimal |
| CAC Amount            | Acquisition Cost / New Customers            | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- Lead ID, channel, campaign, lead status
- Customer ID, acquisition date, acquisition cost

---

## 6. Segmentation & Hierarchies
- Channel: Channel Group > Channel  
- Campaign: Type > Campaign  
- Customer: Segment  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Attribution method (first-touch, last-touch, multi-touch) is documented and applied consistently.
- Only new-to-file customers are counted as acquisitions.

---

## 8. Data Freshness & Cadence
- Leads: daily.
- Acquisitions: daily/weekly.
- Reporting cadence: weekly growth and campaign reviews.

---

## 9. Edge Cases & QA Rules
- Leads without a channel or campaign are flagged.
- Acquisition cost must be non-negative; extreme outliers are capped or reviewed.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Lead fact with channel and campaign.
  - Acquisition fact with cost and customer ID.

---

## 11. Typical Actions
| Action                              | Code | Expected Effect                  |
|-------------------------------------|------|----------------------------------|
| Shift budget to high-conversion channels | D2 | Higher new customer volume       |
| Optimize campaigns with low CAC     | P2   | More efficient acquisition       |
| Improve nurturing for weak stages   | C1   | Higher overall conversion        |

---

## 12. Expected Business Impact
| Dimension | Expected Impact               | Measurement   |
|-----------|-------------------------------|---------------|
| Growth    | +5–10 % new customers        | vs baseline   |
| Efficiency| -10–20 % CAC                 | vs baseline   |

---

## 13. Related Processes
Lead Generation → Nurturing → Sales Handover → Onboarding.

---

## 14. Insights & Learnings
Typical findings include highly effective but underfunded channels and low-performing campaigns with high CAC.

---

## 15. Cross-References
- Related Use Cases:  
  `[CST-001 Customer Retention & Churn Analysis](../CST-001_Customer_Retention_and_Churn/FactSheet.md)`  
  `[CST-004 Campaign Effectiveness](../CST-004_Campaign_Effectiveness/FactSheet.md)`  

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

