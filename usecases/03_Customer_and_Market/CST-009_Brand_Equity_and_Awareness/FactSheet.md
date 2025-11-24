---
id: "CST-009"
title: "Brand Equity & Awareness"
domain: "Customer and Market"
owner: "Head of Brand / Marketing"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Brand Awareness %", "Net Promoter Score (NPS)"]
supports_strategic_kpi_ids: ["mkt.brand.awareness.pct", "crm.nps.index"]
action_codes: ["SP1", "M3", "D2"]
expected_impact: "Higher brand awareness and preference in target segments; stronger funnel performance."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Market.Region>Country",
  "Customer.Segment",
  "Channel",
  "Time.Year>Quarter"
]
filters_default: [
  "Time: Last 8Q",
  "Region: All",
  "Segment: All"
]
qa_asserts: ["RI_OK", "Survey_Base_Sufficient", "Brand_Metrics_Consistent"]
required_kpi_ids: [
  "mkt.brand.awareness.pct",
  "mkt.brand.preference.pct",
  "crm.nps.index"
]
required_kpis:
  mkt.brand.awareness.pct: "Brand Awareness %"
  mkt.brand.preference.pct: "Brand Preference %"
  crm.nps.index: "Net Promoter Score (NPS)"
data_requirements:
  facts:
    - name: fact_brand_survey
      grain: respondent
      primary_key: [RespondentID]
      required_columns:
        - { name: RespondentID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: Region, type: string, role: attribute }
        - { name: Country, type: string, role: attribute }
        - { name: Segment, type: string, role: attribute }
        - { name: "Brand Awareness Flag", type: bool, role: indicator }
        - { name: "Brand Preference Flag", type: bool, role: indicator }
        - { name: "NPS Score", type: int, role: attribute }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
model_mapping:
  "Brand Awareness Flag": "fact_brand_survey[Brand Awareness Flag]"
  "Brand Preference Flag": "fact_brand_survey[Brand Preference Flag]"
  "NPS Score": "fact_brand_survey[NPS Score]"
  "Region": "fact_brand_survey[Region]"
  "Segment": "fact_brand_survey[Segment]"
  "Date": "dim_date[Date]"
---

# Brand Equity & Awareness

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
