---
id: "CST-005"
title: "NPS Analysis"
domain: "Customer and Market"
owner: "Head of Customer Experience / CRM"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Net Promoter Score (NPS)", "Customer Retention %"]
supports_strategic_kpi_ids: ["crm.nps.index", "crm.retention.pct"]
action_codes: ["D3", "M3"]
expected_impact: "+3 pp NPS, +1 pp Retention durch datenbasierte Verbesserungen entlang der Customer Journey."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Customer.Region>Market",
  "Customer.Segment>LoyaltyTier",
  "Touchpoint.Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Segment: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "Responses_Sufficient", "Score_Within_11_11"]
required_kpi_ids: [
  "crm.nps.index",
  "crm.retention.pct",
  "crm.churn.pct"
]
required_kpis:
  crm.nps.index: "NPS Index"
  crm.retention.pct: "Customer Retention %"
  crm.churn.pct: "Churn %"
data_requirements:
  facts:
    - name: fact_nps_survey
      grain: response
      primary_key: [ResponseID]
      required_columns:
        - { name: ResponseID, type: string, role: attribute }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: ResponseDate, type: date, role: date_key }
        - { name: Channel, type: string, role: channel }
        - { name: Touchpoint, type: string, role: attribute }
        - { name: Score, type: int, role: attribute }
        - { name: Comment, type: string, role: attribute }
    - name: fact_customer_status
      grain: customer_month
      primary_key: [CustomerID, SnapshotMonth]
      required_columns:
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: Status, type: string, role: attribute }
        - { name: ChurnFlag, type: bool, role: indicator }
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
    - { from: fact_nps_survey.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_nps_survey.ResponseDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_customer_status.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
    - { from: fact_customer_status.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "NPS Score": "fact_nps_survey[Score]"
  "NPS Comment": "fact_nps_survey[Comment]"
  "Customer": "dim_customer[CustomerID]"
---

# NPS Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** NPS und Kundenfeedback strukturiert analysieren, um schnell die wichtigsten Pain Points und Promoter-Treiber zu identifizieren.
- **Target Audience:** Head of Customer Experience / CRM
- **Business Priority:** High
- **Expected Impact:** +3 pp NPS, +1 pp Retention durch datenbasierte Verbesserungen entlang der Customer Journey.

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
- KPI cards for NPS Index, Customer Retention %, Churn % with Plan/LY deltas.
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