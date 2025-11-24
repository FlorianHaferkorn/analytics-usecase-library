---
id: "COM-010"
title: "Sales Funnel & Win–Loss Analysis"
domain: "Commercial"
owner: "Head of Sales / CRM Lead"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue Growth %", "Customer Retention %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "crm.retention.pct"]
action_codes: ["C1", "D1", "P2"]
expected_impact: "Higher conversion and win rates along the funnel; better pipeline quality."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>SalesTeam",
  "Customer.Segment>Industry",
  "Product.Category>Subcategory",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Sales Stage: All",
  "Segment: All"
]
qa_asserts: ["RI_OK", "Opp_Stage_Consistent", "Pipeline_Reconciles"]
required_kpi_ids: [
  "crm.opportunities.open.amount",
  "crm.opportunities.won.amount",
  "crm.opportunities.win_rate.pct",
  "crm.opportunities.stage_conversion.pct"
]
required_kpis:
  crm.opportunities.open.amount: "Open Pipeline Amount"
  crm.opportunities.won.amount: "Won Opportunities Amount"
  crm.opportunities.win_rate.pct: "Win Rate %"
  crm.opportunities.stage_conversion.pct: "Stage Conversion Rate %"
data_requirements:
  facts:
    - name: fact_opportunity
      grain: opportunity
      primary_key: [OpportunityID]
      required_columns:
        - { name: OpportunityID, type: string, role: attribute }
        - { name: "Opportunity Amount", type: decimal, role: amount }
        - { name: "Close Amount", type: decimal, role: amount }
        - { name: "Open Date", type: date, role: date_key }
        - { name: "Close Date", type: date, role: date_key }
        - { name: "Stage", type: string, role: attribute }
        - { name: "Status", type: string, role: status }
        - { name: "SalesRepID", type: string, role: attribute }
        - { name: "CustomerID", type: string, role: customer_key }
        - { name: OrgID, type: string, role: org_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Area, type: string }
        - { name: SalesTeam, type: string }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: Industry, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_opportunity.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_opportunity.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Opportunity Amount": "fact_opportunity[Opportunity Amount]"
  "Close Amount": "fact_opportunity[Close Amount]"
  "Stage": "fact_opportunity[Stage]"
  "Status": "fact_opportunity[Status]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# Sales Funnel & Win–Loss Analysis

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
