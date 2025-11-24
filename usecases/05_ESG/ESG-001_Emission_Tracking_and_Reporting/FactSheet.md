---
id: "ESG-001"
title: "Emission Tracking & Reporting"
domain: "ESG"
owner: "Head of Sustainability / ESG Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Carbon Emission Intensity", "ESG-Aligned Revenue %"]
supports_strategic_kpi_ids: ["esg.carbon_intensity.tco2e_per_revenue", "esg.aligned_revenue.pct"]
action_codes: ["E1", "S1"]
expected_impact: "-10 % Carbon Intensity, erhÃ¶hte Transparenz fÃ¼r regulatorische Reports."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Site",
  "Emission.Scope>Source",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Scope: 1-3",
  "Site: All"
]
qa_asserts: ["RI_OK", "Scopes_Complete", "Emissions_Reconcile"]
required_kpi_ids: [
  "esg.co2.total.tco2e",
  "esg.carbon_intensity.tco2e_per_revenue",
  "esg.aligned_revenue.pct"
]
required_kpis:
  esg.co2.total.tco2e: "Total CO2 Emissions (tCO2e)"
  esg.carbon_intensity.tco2e_per_revenue: "Carbon Emission Intensity"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
data_requirements:
  facts:
    - name: fact_sustainability
      grain: facility_month
      primary_key: [SiteID, Month]
      required_columns:
        - { name: SiteID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: Scope, type: string, role: attribute }
        - { name: Emission_tCO2e, type: decimal, role: amount }
    - name: fact_sales
      grain: org_month
      primary_key: [OrgID, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: NetSalesAmount, type: decimal, role: amount }
        - { name: ESGAlignedRevenueAmount, type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
    - name: dim_site
      grain: site
      primary_key: [SiteID]
      required_columns:
        - { name: SiteName, type: string }
        - { name: SiteType, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_sustainability.SiteID, to: dim_site.SiteID, cardinality: many-to-one, direction: single }
    - { from: fact_sustainability.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Total CO2 Emissions": "fact_sustainability[Emission_tCO2e]"
  "Net Sales Amount": "fact_sales[NetSalesAmount]"
  "ESG-Aligned Revenue Amount": "fact_sales[ESGAlignedRevenueAmount]"
---

# Emission Tracking & Reporting

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
