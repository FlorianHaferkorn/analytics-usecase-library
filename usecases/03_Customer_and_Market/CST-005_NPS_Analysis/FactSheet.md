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

# Use Case Fact Sheet

## 1. Business Goal
NPS und Kundenfeedback strukturiert analysieren, um schnell die wichtigsten Pain Points und Promoter-Treiber zu identifizieren.

## 2. Business Questions
- Wie entwickelt sich NPS Ã¼ber Zeit, Segmente und KanÃ¤le?
- Welche Themen und Touchpoints treiben detractor vs. promoter Feedback?
- Wie hÃ¤ngen NPS, Retention und Churn zusammen?

## 3. Scope & Assumptions
- Es werden standardisierte NPS-Surveys (Skala 0–10) genutzt.
- Kommentare sind unstrukturiert, kÃ¶nnen aber fÃ¼r Text-Mining genutzt werden.

## 4. Target Users & Decisions
- Zielgruppe: Customer Experience, CRM, Service- und Produktverantwortliche.
- Entscheidungen: Journey-Verbesserungen, Priorisierung von MaÃŸnahmen, Follow-up mit Detractors.

## 5. KPIs & Drivers (Overview)
- NPS Index, Response Rate, Retention %, Churn %.
- Treiber: Segment, Kanal, Touchpoint, Themen aus Kommentaren.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- Response-Stichprobe muss ausreichend groÃŸ und reprÃ¤sentativ sein.
- Kundenstatus und NPS-Response mÃ¼ssen sauber verknÃ¼pft sein.

## 8. Page Layout / Storyboard
- Overview: NPS Scorecards, Zeitreihe, Segment/Kanal-Matrix.
- Drivers: Verteilungen (Promoter/Passive/Detractor), Drill-down nach Touchpoint und Kommentar-Themen.
