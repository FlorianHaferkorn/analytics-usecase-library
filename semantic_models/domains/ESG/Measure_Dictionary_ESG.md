# Measure Dictionary - ESG

Schema: see `/_includes/kpi_catalog/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: Carbon Emission Intensity
  is_kpi_measure: true
  kpi_id_ref: esg.carbon_intensity.tco2e_per_revenue
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Total CO Emissions (tCO2)],[Net Sales Amount])
    formatString: '0.00'
  documentation:
    description: Total greenhouse gas emissions divided by revenue for the selected period (carbon intensity).
    notes: ''
  governance:
    owner: ESG BI
    status: active
    version: v2.0
    last_review: 12.10.2025
  dependencies:
    measures:
    - Net Sales Amount
    columns:
    - fact_sustainability.CO2_Emissions
    - fact_sales.Net Sales Amount
- measure_name: ESG-Aligned Revenue %
  is_kpi_measure: true
  kpi_id_ref: esg.aligned_revenue.pct
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([ESG-Aligned Revenue Amount],[Net Sales Amount])
    formatString: 0.0 %
  documentation:
    description: Share of revenue that meets EU Taxonomy criteria.
    notes: ''
  governance:
    owner: Finance Reporting
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 01_Strategy
  dependencies:
    measures:
    - ESG-Aligned Revenue Amount
    - Net Sales Amount
    columns:
    - fact_esg.RevenueAligned
    - fact_sales.Net Sales Amount
- measure_name: Renewable Energy (kWh)
  is_kpi_measure: true
  kpi_id_ref: esg.energy.renewable_kwh
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0'
  documentation:
    description: Total renewable energy consumption
    notes: ''
  governance:
    owner: Sustainability Data Team
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Total Energy (kWh)
  is_kpi_measure: true
  kpi_id_ref: esg.energy.total_kwh
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0'
  documentation:
    description: Total energy consumption
    notes: ''
  governance:
    owner: Sustainability Data Team
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: Total CO2 Emissions (tCO2e)
  is_kpi_measure: true
  kpi_id_ref: esg.co2.total.tco2e
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: '// TODO: add expression'
    formatString: '#,0'
  documentation:
    description: Aggregated Scope 1-3 CO2e
    notes: ''
  governance:
    owner: Sustainability Data Team
    status: active
    version: v1.0
    last_review: 04.11.2025
- measure_name: LTIFR
  is_kpi_measure: true
  kpi_id_ref: esg.ltifr.rate
  semantic_model: ESG_SemanticModel
  category: KPI
  expression:
    dax: DIVIDE([Lost Time Injuries],[Hours Worked]) * 1000000
    formatString: '0.00'
  documentation:
    description: Lost Time Injury Frequency Rate.
    notes: ''
  governance:
    owner: Safety Office
    status: active
    version: v1.0
    last_review: 11.11.2025
  display_folder: 02_Safety
  dependencies:
    measures:
    - Lost Time Injuries
    - Hours Worked
    columns:
    - fact_safety.LostTimeInjuries
    - fact_hr.HoursWorked
```
