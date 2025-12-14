# Measure Dictionary - ESG

Schema: see `/semantic_models/Domain_Measure_Dictionary_Schema.md`

```yaml
- measure_name: "Carbon Emission Intensity"
  is_kpi_measure: true
  kpi_id_ref: "esg.carbon_intensity.tco2e_per_revenue"
  semantic_model: "ESG_SemanticModel"
  display_folder: "01_Carbon"
  category: "KPI"
  expression:
    dax: |
      VAR Emissions = SUM ( fact_sustainability[CO2 Emissions] )
      VAR Revenue   = SUM ( fact_sales[Net Sales Amount] )
      RETURN DIVIDE ( Emissions, Revenue )
    formatString: "0.000 tCO2e per revenue"
  documentation:
    description: "Total CO2e emissions per revenue."
    notes: |
      Grain: quarter (aggregated from month). Unit: tCO2e per revenue.
      Lineage: fact_sustainability[CO2 Emissions], fact_sales[Net Sales Amount].
      QA: Scope coverage complete; revenue consistent; DIVIDE guard; currency alignment.
  dependencies:
    columns:
      - "fact_sustainability[CO2 Emissions]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "ESG-Aligned Revenue %"
  is_kpi_measure: true
  kpi_id_ref: "esg.aligned_revenue.pct"
  semantic_model: "ESG_SemanticModel"
  display_folder: "02_Revenue"
  category: "KPI"
  expression:
    dax: |
      VAR Aligned = SUM ( fact_sales[ESG Aligned Revenue] )
      VAR Revenue = SUM ( fact_sales[Net Sales Amount] )
      RETURN DIVIDE ( Aligned, Revenue )
    formatString: "0.0%"
  documentation:
    description: "Share of revenue classified as ESG-aligned."
    notes: |
      Grain: quarter (aggregated from month). Unit: %.
      Lineage: fact_sales[ESG Aligned Revenue], fact_sales[Net Sales Amount].
      QA: Classification rules documented; Net Sales > 0; taxonomy version tracked.
  dependencies:
    columns:
      - "fact_sales[ESG Aligned Revenue]"
      - "fact_sales[Net Sales Amount]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Renewable Energy kWh"
  is_kpi_measure: true
  kpi_id_ref: "esg.energy.renewable_kwh"
  semantic_model: "ESG_SemanticModel"
  display_folder: "03_Energy"
  category: "KPI"
  expression:
    dax: "SUM(fact_energy[Renewable kWh])"
    formatString: "#,0 kWh"
  documentation:
    description: "Renewable energy consumed."
    notes: |
      Grain: month. Unit: kWh.
      Lineage: fact_energy[Renewable kWh].
      QA: Metering completeness; avoid duplicates.
  dependencies:
    columns:
      - "fact_energy[Renewable kWh]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Total Energy kWh"
  is_kpi_measure: true
  kpi_id_ref: "esg.energy.total_kwh"
  semantic_model: "ESG_SemanticModel"
  display_folder: "03_Energy"
  category: "KPI"
  expression:
    dax: "SUM(fact_energy[Total kWh])"
    formatString: "#,0 kWh"
  documentation:
    description: "Total energy consumed."
    notes: |
      Grain: month. Unit: kWh.
      Lineage: fact_energy[Total kWh].
      QA: Metering completeness; consistent units.
  dependencies:
    columns:
      - "fact_energy[Total kWh]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "Total CO2 Emissions"
  is_kpi_measure: true
  kpi_id_ref: "esg.co2.total.tco2e"
  semantic_model: "ESG_SemanticModel"
  display_folder: "01_Carbon"
  category: "KPI"
  expression:
    dax: "SUM(fact_sustainability[CO2 Emissions])"
    formatString: "#,0.0 tCO2e"
  documentation:
    description: "Total CO2 equivalent emissions."
    notes: |
      Grain: month. Unit: tCO2e.
      Lineage: fact_sustainability[CO2 Emissions].
      QA: Scopes complete; factors documented.
  dependencies:
    columns:
      - "fact_sustainability[CO2 Emissions]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"

- measure_name: "LTIFR"
  is_kpi_measure: true
  kpi_id_ref: "esg.ltifr.rate"
  semantic_model: "ESG_SemanticModel"
  display_folder: "04_Safety"
  category: "KPI"
  expression:
    dax: |
      VAR Injuries = SUM ( fact_safety[LTIs] )
      VAR Hours    = SUM ( fact_safety[Hours Worked] )
      RETURN DIVIDE ( Injuries, Hours ) * 1000000
    formatString: "0.000"
  documentation:
    description: "Lost time injuries per million hours worked."
    notes: |
      Grain: month. Unit: rate.
      Lineage: fact_safety[LTIs], fact_safety[Hours Worked].
      QA: Hours > 0; injury classification consistent; include contractors per policy.
  dependencies:
    columns:
      - "fact_safety[LTIs]"
      - "fact_safety[Hours Worked]"
  governance:
    owner: "Sustainability Analytics"
    status: "draft"
    version: "v1.2"
    last_review: "TBD"
```
