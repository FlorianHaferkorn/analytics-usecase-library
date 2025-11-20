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

# Use Case Fact Sheet

## 1. Business Goal
Energieverbrauch und -kosten senken und gleichzeitig den Anteil erneuerbarer Energie erhÃ¶hen.

## 2. Business Questions
- Welche Sites haben den hÃ¶chsten Energieverbrauch und die schlechteste Effizienz?
- Wie hoch ist der Anteil erneuerbarer Energie, und wo gibt es Potenzial?

## 3. Scope & Assumptions
- Nur Standorte mit vollstÃ¤ndigem ZÃ¤hler- und Kosten-Setup werden berÃ¼cksichtigt.

## 4. Target Users & Decisions
- Zielgruppe: Sustainability, Operations, Facility Management.
- Entscheidungen: EffizienzmaÃŸnahmen, Contracting, Investitionen in erneuerbare Energie.

## 5. KPIs & Drivers (Overview)
- Renewable Energy (kWh), Total Energy (kWh), Energy Cost per Unit, Carbon Intensity.

## 6. Required KPIs (Detail)
Siehe `required_kpi_ids` in der Front Matter.

## 7. Data & Modelling Notes
- Energie- und Kostendaten mÃ¼ssen mit Finance abgeglichen sein.

## 8. Page Layout / Storyboard
- Overview: Energieverbrauch, Kosten und Intensity nach Site.
- Drivers: Quelle/Carrier, Zeitverlauf, EffizienzmaÃŸnahmen.
