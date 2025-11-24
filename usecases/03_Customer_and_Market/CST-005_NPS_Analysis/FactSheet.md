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

# NPS Analysis

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
