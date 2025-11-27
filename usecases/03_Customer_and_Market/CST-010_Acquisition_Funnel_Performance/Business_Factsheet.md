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

# Acquisition Funnel Performance - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and optimize the performance of the acquisition funnel from lead to new customer across channels and campaigns.

---
- **Target Audience:** Head of Marketing / Growth Lead
- **Business Priority:** High
- **Expected Impact:** Higher conversion along the acquisition funnel; lower cost per acquired customer.

## 2. Core Questions
- How many leads and new customers do we generate per channel and campaign?
- What are the conversion rates from lead to customer across funnel stages?
- What is the cost per acquired customer (CAC) by channel and campaign?
- Which campaigns and channels provide the best ROI?
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
- KPI cards for Leads Count, New Customers Acquired, Conversion Rate %, Customer Acquisition Cost (CAC) with Plan/LY deltas.
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