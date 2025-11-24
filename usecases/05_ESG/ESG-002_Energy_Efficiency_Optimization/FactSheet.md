---
id: "ESG-002"
title: "Energy Efficiency Optimization"
domain: "ESG"
owner: "Head of Sustainability / Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Energy Efficiency %", "Carbon Emission Intensity"]
supports_strategic_kpi_ids: ["esg.carbon_intensity.tco2e_per_revenue", "esg.energy.renewable_kwh"]
action_codes: ["S1", "M1"]
expected_impact: "-8 % Energy Cost, -5 % CO2 Intensity durch Effizienz- und Fuel-Switch-MaÃŸnahmen."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Site",
  "Energy.Source>Carrier",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Site: All",
  "Source: All"
]
qa_asserts: ["RI_OK", "Energy_Reconcile", "Intensity_Within_Range"]
required_kpi_ids: [
  "esg.energy.renewable_kwh",
  "esg.energy.total_kwh",
  "esg.carbon_intensity.tco2e_per_revenue"
]
required_kpis:
  esg.energy.renewable_kwh: "Renewable Energy (kWh)"
  esg.energy.total_kwh: "Total Energy (kWh)"
  esg.carbon_intensity.tco2e_per_revenue: "Carbon Emission Intensity"
data_requirements:
  facts:
    - name: fact_energy
      grain: site_month
      primary_key: [SiteID, Month]
      required_columns:
        - { name: SiteID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: Renewable_kWh, type: decimal, role: amount }
        - { name: Total_kWh, type: decimal, role: amount }
        - { name: EnergyCostAmount, type: decimal, role: amount }
  dims:
    - name: dim_site
      grain: site
      primary_key: [SiteID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_energy.SiteID, to: dim_site.SiteID, cardinality: many-to-one, direction: single }
    - { from: fact_energy.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Renewable Energy (kWh)": "fact_energy[Renewable_kWh]"
  "Total Energy (kWh)": "fact_energy[Total_kWh]"
  "Energy Cost Amount": "fact_energy[EnergyCostAmount]"
---

# Energy Efficiency Optimization

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
