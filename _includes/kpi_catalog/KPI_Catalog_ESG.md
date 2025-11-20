# KPI Catalog - ESG (Environment, Social & Governance)

---

Schema: see `/_includes/kpi_catalog/SCHEMA.md`

## KPIs - Strategic
```yaml
- kpi_id: "esg.carbon_intensity.tco2e_per_revenue"
  kpi_key: "Carbon Emission Intensity (tCO2 / Δ Revenue)"
  kpi_type: "strategic"
  strategic_ref: "Carbon Emission Intensity"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref:
    - "ESG-001"
  depends_on:
    - "Total CO₂ Emissions (tCO2)"
    - "Net Sales Amount"
  depends_on_ids:
    - "sales.net_sales.amount"
  calc_type: "ratio"
  refresh: "quarterly"
  status: "Active"
  business:
    purpose:
      "Measures greenhouse gas emissions relative to revenue."
    definition:
      "Total CO₂ Emissions / Net Sales Amount"
    grain_scope:
      "Company level, aggregated quarterly."
    unit_format:
      "tCO2 / €m"
    interpretation:
      "Lower values indicate improved carbon efficiency."
  technical:
    dax_name:
      "Carbon Emission Intensity"
    dax_expression:
      "DIVIDE([Total CO₂ Emissions (tCO2)],[Net Sales Amount])"
    lineage:
      - "fact_sustainability.CO2_Emissions"
      - "fact_sales.Net Sales Amount"
    source_grain:
      "facility"
    source_column_ref:
      "fact_sustainability.co2_tons"
    source_system:
      "Sustainability Platform"
    formatString:
      "0.00"
    description:
      "Total greenhouse gas emissions divided by revenue for the selected period (carbon intensity)."
    verified:
      "true"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "ESG BI"
    steward:
      "Environmental Analyst"
    review_cycle:
      "semi-annual"
    validation_process:
      "manual review"
    qa_rules:
      "Scopes 1–3 fully reported for all sites"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.95"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


```yaml
kpi_key: "Renewable Energy Share %"
  kpi_type: "strategic"
  strategic_ref: "Renewable Energy Share %"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: "ESG-002"
  depends_on:
    - "Renewable Energy (kWh)"
    - "Total Energy (kWh)"
  depends_on_ids:
    - "esg.energy.renewable_kwh"
    - "esg.energy.total_kwh"
  calc_type: "ratio"
  refresh: "quarterly"
  status: "Active"
  business:
    purpose:
      "Measures share of renewable energy in total consumption."
    definition:
      "Renewable Energy (kWh) / Total Energy (kWh)"
    grain_scope:
      "Facility level; aggregated companywide."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Higher share indicates greener operations."
  technical:
    dax_name:
      "Renewable Energy Share %"
    dax_expression:
      "DIVIDE([Renewable Energy (kWh)],[Total Energy (kWh)])"
    lineage:
      - "fact_energy.Renewable_kWh"
      - "fact_energy.Total_kWh"
    source_grain:
      "facility"
    source_column_ref:
      - "fact_energy.renewable_kwh"
      - "fact_energy.total_kwh"
    source_system:
      "Energy Management System"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "ESG BI"
    steward:
      "Energy Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "automated"
    qa_rules:
      "Renewable Share % within [0;100]"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.97"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


## KPIs - Supporting / Diagnostic
```yaml
kpi_key: "Scope 1 Emissions (tCO2)"
  kpi_type: "supporting"
  strategic_ref: "Carbon Emission Intensity"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: "ESG-001"
  depends_on: "Fuel Consumption (kWh)"
  calc_type: "amount"
  refresh: "quarterly"
  status: "Active"
  business:
    purpose:
      "Direct emissions from owned or controlled sources."
    definition:
      "Fuel × Emission Factor"
    grain_scope:
      "Facility level."
    unit_format:
      "tCO2"
    interpretation:
      "Core contributor to total CO₂ emissions."
  technical:
    dax_name:
      "Scope 1 Emissions"
    dax_expression:
      "SUM(fact_sustainability[Scope1_Emissions])"
    lineage:
      "fact_sustainability.Scope1_Emissions"
    source_grain:
      "facility"
    source_column_ref:
      "fact_sustainability.scope1_tons"
    source_system:
      "Sustainability Platform"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "ESG BI"
    steward:
      "Environmental Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "No negative emissions values"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "0.98"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


## 3. Base Measures
```yaml
kpi_key: "Total Energy (kWh)"
  kpi_type: "supporting"
  strategic_ref: "Renewable Energy Share %"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: "ESG-002"
  calc_type: "amount"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Total electricity and heat consumption from all sources."
    definition:
      "Sum of electricity, heating, and fuel energy consumption."
    grain_scope:
      "Facility and energy meter level."
    unit_format:
      "kWh"
    interpretation:
      "Represents total energy demand."
  technical:
    dax_name:
      "Total Energy (kWh)"
    dax_expression:
      "SUM(fact_energy[Total Energy (kWh)])"
    lineage:
      "fact_energy.Total_kWh"
    source_grain:
      "facility"
    source_column_ref:
      "fact_energy.total_kwh"
    source_system:
      "Energy Management System"
    verified:
      "true"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "ESG BI"
    steward:
      "Energy Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "automated"
    qa_rules:
      "Energy values must be > 0"
    version:
      "v2.0"
    last_review:
      "12.10.2025"
  metadata_quality:
    completeness_score:
      "1.00"
    lineage_verified:
      "true"
    copilot_ready:
      "true"
```


---

## 4. Governance Summary
| Metric | Value |
|--------|--------|
| **Total KPIs (ESG)** | 31 |
| **Completeness Score (avg)** | 0.96 |
| **Lineage Verified** | 100 % |
| **Copilot Ready** | 100 % |
| **Review Cycle** | Quarterly |
| **Business Owner** | Head of Sustainability |
| **Data Owner** | ESG BI |
| **Steward** | Environmental Analyst |
| **Validation Process** | Manual Review |

---

_Last updated: 04.11.2025_
```yaml
- kpi_id: "esg.aligned_revenue.pct"
  kpi_key: "ESG-Aligned Revenue %"
  kpi_type: "strategic"
  strategic_ref: "ESG-Aligned Revenue %"
  impact_dimension: "ESG"
  domain_tag: ["Corporate & Strategy"]
  use_case_ref:
    - "COR-003"
    - "COR-004"
  depends_on:
    - "ESG-Aligned Revenue Amount"
    - "Net Sales Amount"
  calc_type: "rate"
  refresh: "quarterly"
  status: "Active"
  business:
    purpose:
      "Tracks portion of revenue classified as environmentally sustainable."
    definition:
      "ESG-aligned revenue / total revenue."
    grain_scope:
      "Legal entity / portfolio."
    unit_format:
      "% (1 decimal)"
    interpretation:
      "Used to demonstrate CSRD / EU Taxonomy compliance."
  technical:
    dax_name:
      "ESG-Aligned Revenue %"
    dax_expression:
      "DIVIDE([ESG-Aligned Revenue Amount],[Net Sales Amount])"
    displayFolder:
      "01_Strategy"
    formatString:
      "0.0 %"
    description:
      "Share of revenue that meets EU Taxonomy criteria."
    lineage:
      - "fact_esg.RevenueAligned"
      - "fact_sales.Net Sales Amount"
    source_system:
      "Sustainability / Finance"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "Finance Reporting"
    steward:
      "ESG Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Mapping to taxonomy activity documented"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.8"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```




```yaml
- kpi_id: "esg.energy.renewable_kwh"
  kpi_key: "Renewable Energy (kWh)"
  kpi_type: "supporting"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  calc_type: "amount"
  business:
    purpose:
      "Measure renewable energy consumption as input to carbon and taxonomy KPIs."
    definition:
      "Total renewable energy consumed in the period (e.g., solar, wind, certified green electricity)."
    grain_scope:
      "Site/region; aggregated monthly or yearly."
    unit_format:
      "kWh"
  technical:
    dax_name:
      "Renewable Energy (kWh)"
    formatString:
      "#,0"
    description:
      "Total renewable energy consumption"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "Sustainability Data Team"
    steward:
      "Energy Reporting Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Reconciles to energy metering and utility invoices within acceptable tolerance; non-negative values only."
    version:
      "v1.0"
    last_review:
      "2025-11-04"
```


```yaml
- kpi_id: "esg.energy.total_kwh"
  kpi_key: "Total Energy (kWh)"
  kpi_type: "supporting"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  calc_type: "amount"
  business:
    purpose:
      "Measure total energy consumption as base for carbon emissions and efficiency KPIs."
    definition:
      "Total energy consumed in the period across all sources."
    grain_scope:
      "Site/region; aggregated monthly or yearly."
    unit_format:
      "kWh"
  technical:
    dax_name:
      "Total Energy (kWh)"
    formatString:
      "#,0"
    description:
      "Total energy consumption"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "Sustainability Data Team"
    steward:
      "Energy Reporting Analyst"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Reconciles to energy metering and utility invoices within acceptable tolerance; non-negative values only."
    version:
      "v1.0"
    last_review:
      "2025-11-04"
```


```yaml
- kpi_id: "esg.co2.total.tco2e"
  kpi_key: "Total CO2 Emissions (tCO2e)"
  kpi_type: "supporting"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  calc_type: "amount"
  business:
    purpose:
      "Track total greenhouse gas emissions (CO2e) as core input for climate targets and disclosures."
    definition:
      "Sum of Scope 1, Scope 2 and relevant Scope 3 emissions expressed in tCO2e."
    grain_scope:
      "Company/site/region; aggregated monthly or yearly."
    unit_format:
      "tCO2e"
  technical:
    dax_name:
      "Total CO2 Emissions (tCO2e)"
    formatString:
      "#,0"
    description:
      "Aggregated Scope 1-3 CO2e"
    verified:
      "false"
  governance:
    business_owner:
      "Head of Sustainability"
    data_owner:
      "Sustainability Data Team"
    steward:
      "Carbon Accounting Specialist"
    review_cycle:
      "quarterly"
    validation_process:
      "manual review"
    qa_rules:
      "Non-negative values; reconciles to carbon accounting system and audited disclosure within agreed tolerance."
    version:
      "v1.0"
    last_review:
      "2025-11-04"
```





```yaml
- kpi_id: "esg.ltifr.rate"
  kpi_key: "Lost Time Injury Frequency Rate"
  kpi_type: "supporting"
  impact_dimension: "ESG"
  domain_tag: ["Safety"]
  use_case_ref:
    - "COR-003"
  depends_on:
    - "Lost Time Injuries"
    - "Hours Worked"
  calc_type: "rate"
  refresh: "monthly"
  status: "Active"
  business:
    purpose:
      "Measures safety incidents resulting in lost time per hours worked."
    definition:
      "(Lost Time Injuries / Hours Worked) * 1,000,000"
    grain_scope:
      "Site / region."
    unit_format:
      "rate"
    interpretation:
      "Lower rate indicates better safety performance."
  technical:
    dax_name:
      "LTIFR"
    dax_expression:
      "DIVIDE([Lost Time Injuries],[Hours Worked]) * 1000000"
    displayFolder:
      "02_Safety"
    formatString:
      "0.00"
    description:
      "Lost Time Injury Frequency Rate."
    lineage:
      - "fact_safety.LostTimeInjuries"
      - "fact_hr.HoursWorked"
    source_system:
      "HSE / HR"
    verified:
      "false"
  governance:
    business_owner:
      "Head of HSE"
    data_owner:
      "Safety Office"
    steward:
      "HSE Analyst"
    review_cycle:
      "monthly"
    validation_process:
      "manual review"
    qa_rules:
      "Hours worked reconciled with HR totals"
    version:
      "v1.0"
    last_review:
      "11.11.2025"
  metadata_quality:
    completeness_score:
      "0.8"
    lineage_verified:
      "false"
    copilot_ready:
      "true"
```















