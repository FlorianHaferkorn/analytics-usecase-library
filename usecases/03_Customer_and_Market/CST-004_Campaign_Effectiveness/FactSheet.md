---
id: "CST-004"
title: "Campaign Effectiveness"
domain: "Customer and Market"
owner: "Head of Marketing / CRM"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Marketing ROI %", "Conversion Rate %", "Customer Retention %"]
supports_strategic_kpi_ids: ["sales.promo.roi.pct", "crm.reactivation.pct", "crm.retention.pct"]
action_codes: ["D2", "M3"]
expected_impact: "+5 pp Campaign ROI, +2 pp Retention, effizientere Budgetallokation."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Campaign.Type>Channel>Creative",
  "Customer.Segment>LoyaltyTier",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Campaign Type: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "ROI_Within_Range", "Spend_Reconciles"]
required_kpi_ids: [
  "sales.promo.roi.pct",
  "sales.promo.uplift_pct",
  "crm.reactivation.pct",
  "crm.at_risk_share.pct",
  "crm.retention.pct"
]
required_kpis:
  sales.promo.roi.pct: "Campaign ROI %"
  sales.promo.uplift_pct: "Uplift % vs. Baseline"
  crm.reactivation.pct: "Reactivation Rate %"
  crm.at_risk_share.pct: "At-Risk Share %"
  crm.retention.pct: "Retention %"
data_requirements:
  facts:
    - name: fact_campaign
      grain: campaign_customer
      primary_key: [CampaignID, CustomerID]
      required_columns:
        - { name: CampaignID, type: string, role: campaign_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: Channel, type: string, role: channel }
        - { name: SpendAmount, type: decimal, role: amount }
        - { name: ResponseFlag, type: bool, role: indicator }
        - { name: ConversionFlag, type: bool, role: indicator }
        - { name: RevenueAmount, type: decimal, role: amount }
  dims:
    - name: dim_campaign
      grain: campaign
      primary_key: [CampaignID]
      required_columns:
        - { name: CampaignName, type: string }
        - { name: CampaignType, type: string }
        - { name: StartDate, type: date }
        - { name: EndDate, type: date }
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
        - { name: LoyaltyTier, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_campaign.CampaignID, to: dim_campaign.CampaignID, cardinality: many-to-one, direction: single }
    - { from: fact_campaign.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Campaign": "dim_campaign[CampaignID]"
  "Customer": "dim_customer[CustomerID]"
  "Campaign Spend": "fact_campaign[SpendAmount]"
  "Campaign Revenue": "fact_campaign[RevenueAmount]"
---

# Campaign Effectiveness

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
