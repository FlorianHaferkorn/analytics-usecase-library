# KPI Catalog - ESG

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: esg.carbon_intensity.tco2e_per_revenue
  kpi_key: Carbon Emission Intensity (tCO2e per revenue)
  kpi_type: strategic
  impact_dimension: ESG
  domain_tag:
  - Sustainability
  use_case_ref:
  - ESG-001
  calc_type: ratio
  business:
    purpose: Measures greenhouse gas emissions relative to revenue.
    definition: Total CO2e Emissions / Net Sales Amount.
    grain_scope: Company level, aggregated quarterly (scopes 1-3).
    unit_format: tCO2e per revenue
    interpretation: Lower values indicate improved carbon efficiency.
  technical:
    dax_name: Carbon Emission Intensity
    depends_on_measures:
    - Net Sales Amount
    lineage:
    - fact_sustainability.CO2_Emissions
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sustainability
    data_owner: ESG BI
    steward: Environmental Analyst
    review_cycle: semi-annual
    validation_process: manual review
    qa_rules:
    - Scopes 1-3 fully reported for all sites; revenue currency aligned
    version: v2.0
  metadata_quality:
    completeness_score: 0.95
    last_review: 12.10.2025
- kpi_id: esg.aligned_revenue.pct
  kpi_key: ESG-Aligned Revenue %
  kpi_type: strategic
  impact_dimension: ESG
  domain_tag:
  - Corporate & Strategy
  use_case_ref:
  - COR-003
  - COR-004
  calc_type: rate
  business:
    purpose: Tracks portion of revenue classified as environmentally sustainable.
    definition: ESG-aligned revenue / total revenue.
    grain_scope: Legal entity / portfolio.
    unit_format: '% (1 decimal)'
    interpretation: Used to demonstrate CSRD / EU Taxonomy compliance.
  technical:
    dax_name: ESG-Aligned Revenue %
    depends_on_measures:
    - ESG-Aligned Revenue Amount
    - Net Sales Amount
    lineage:
    - fact_esg.RevenueAligned
    - fact_sales.Net Sales Amount
  governance:
    business_owner: Head of Sustainability
    data_owner: Finance Reporting
    steward: ESG Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Mapping to taxonomy activity documented
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: esg.energy.renewable_kwh
  kpi_key: Renewable Energy (kWh)
  kpi_type: supporting
  impact_dimension: ESG
  domain_tag:
  - Sustainability
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Measure renewable energy consumption as input to carbon and taxonomy KPIs.
    definition: Total renewable energy consumed in the period (e.g., solar, wind, certified green electricity).
    grain_scope: Site/region; aggregated monthly or yearly.
    unit_format: kWh
    interpretation: Higher share supports ESG alignment and lower carbon intensity.
  technical:
    dax_name: Renewable Energy (kWh)
    depends_on_measures: []
    lineage:
    - fact_energy.Renewable kWh
  governance:
    business_owner: Head of Sustainability
    data_owner: Sustainability Data Team
    steward: Energy Reporting Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to energy metering and utility invoices within acceptable tolerance; non-negative values only.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: esg.energy.total_kwh
  kpi_key: Total Energy (kWh)
  kpi_type: supporting
  impact_dimension: ESG
  domain_tag:
  - Sustainability
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Measure total energy consumption as base for carbon emissions and efficiency KPIs.
    definition: Total energy consumed in the period across all sources.
    grain_scope: Site/region; aggregated monthly or yearly.
    unit_format: kWh
    interpretation: Monitor trend; input to carbon intensity calculations.
  technical:
    dax_name: Total Energy (kWh)
    depends_on_measures: []
    lineage:
    - fact_energy.Total kWh
  governance:
    business_owner: Head of Sustainability
    data_owner: Sustainability Data Team
    steward: Energy Reporting Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to energy metering and utility invoices within acceptable tolerance; non-negative values only.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: esg.co2.total.tco2e
  kpi_key: Total CO2 Emissions (tCO2e)
  kpi_type: supporting
  impact_dimension: ESG
  domain_tag:
  - Sustainability
  use_case_ref: []
  calc_type: amount
  business:
    purpose: Track total greenhouse gas emissions (CO2e) as core input for climate targets and disclosures.
    definition: Sum of Scope 1, Scope 2 and relevant Scope 3 emissions expressed in tCO2e.
    grain_scope: Company/site/region; aggregated monthly or yearly.
    unit_format: tCO2e
    interpretation: Higher share supports ESG alignment and lower carbon intensity.
  technical:
    dax_name: Total CO2 Emissions (tCO2e)
    depends_on_measures: []
    lineage:
    - fact_energy.Renewable kWh
  governance:
    business_owner: Head of Sustainability
    data_owner: Sustainability Data Team
    steward: Carbon Accounting Specialist
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative values; reconciles to carbon accounting system and audited disclosure within agreed tolerance.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
- kpi_id: esg.ltifr.rate
  kpi_key: Lost Time Injury Frequency Rate
  kpi_type: supporting
  impact_dimension: ESG
  domain_tag:
  - Safety
  use_case_ref:
  - COR-003
  calc_type: rate
  business:
    purpose: Measures safety incidents resulting in lost time per hours worked.
    definition: (Lost Time Injuries / Hours Worked) * 1,000,000
    grain_scope: Site / region.
    unit_format: rate
    interpretation: Lower rate indicates better safety performance.
  technical:
    dax_name: LTIFR
    depends_on_measures:
    - Lost Time Injuries
    - Hours Worked
    lineage:
    - fact_safety.LostTimeInjuries
    - fact_hr.HoursWorked
  governance:
    business_owner: Head of HSE
    data_owner: Safety Office
    steward: HSE Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Hours worked reconciled with HR totals
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
```
