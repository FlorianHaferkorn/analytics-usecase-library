# KPI Catalog – ESG (Environment, Social & Governance)

---

## 1. Strategic KPIs
```yaml
- kpi_key: "Carbon Emission Intensity (tCO₂e / € Revenue)"
  kpi_type: "strategic"
  strategic_ref: "Carbon Emission Intensity"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: ["ESG-001"]
  depends_on: ["Total CO₂ Emissions (tCO₂e)","Net Sales Amount"]
  calc_type: ratio
  refresh: quarterly
  status: Active
  business:
    purpose: "Measures greenhouse gas emissions relative to revenue."
    definition: "Total CO₂ Emissions / Net Sales Amount"
    grain_scope: "Company level, aggregated quarterly."
    unit_format: "tCO₂e / €m"
    interpretation: "Lower values indicate improved carbon efficiency."
  technical:
    dax_name: "Carbon Emission Intensity"
    dax_expression: "DIVIDE([Total CO₂ Emissions (tCO₂e)],[Net Sales Amount])"
    lineage: ["fact_sustainability.CO2_Emissions","fact_sales.Net Sales Amount"]
    source_grain: "facility"
    source_column_ref: ["fact_sustainability.co2_tons"]
    source_system: "Sustainability Platform"
    verified: true
  governance:
    business_owner: "Head of Sustainability"
    data_owner: "ESG BI"
    steward: "Environmental Analyst"
    review_cycle: "semi-annual"
    validation_process: "manual review"
    qa_rules:
      - "Scopes 1–3 fully reported for all sites"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.95
    lineage_verified: true
    copilot_ready: true
```

```yaml
- kpi_key: "Renewable Energy Share %"
  kpi_type: "strategic"
  strategic_ref: "Renewable Energy Share %"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: ["ESG-002"]
  depends_on: ["Renewable Energy (kWh)","Total Energy (kWh)"]
  calc_type: ratio
  refresh: quarterly
  status: Active
  business:
    purpose: "Measures share of renewable energy in total consumption."
    definition: "Renewable Energy (kWh) / Total Energy (kWh)"
    grain_scope: "Facility level; aggregated companywide."
    unit_format: "% (1 decimal)"
    interpretation: "Higher share indicates greener operations."
  technical:
    dax_name: "Renewable Energy Share %"
    dax_expression: "DIVIDE([Renewable Energy (kWh)],[Total Energy (kWh)])"
    lineage: ["fact_energy.Renewable_kWh","fact_energy.Total_kWh"]
    source_grain: "facility"
    source_column_ref: ["fact_energy.renewable_kwh","fact_energy.total_kwh"]
    source_system: "Energy Management System"
    verified: true
  governance:
    business_owner: "Head of Sustainability"
    data_owner: "ESG BI"
    steward: "Energy Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "Renewable Share % within [0;100]"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.97
    lineage_verified: true
    copilot_ready: true
```

## 2. Supporting / Diagnostic KPIs
```yaml
- kpi_key: "Scope 1 Emissions (tCO₂e)"
  kpi_type: "supporting"
  strategic_ref: "Carbon Emission Intensity"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: ["ESG-001"]
  depends_on: ["Fuel Consumption (kWh)"]
  calc_type: amount
  refresh: quarterly
  status: Active
  business:
    purpose: "Direct emissions from owned or controlled sources."
    definition: "Fuel × Emission Factor"
    grain_scope: "Facility level."
    unit_format: "tCO₂e"
    interpretation: "Core contributor to total CO₂ emissions."
  technical:
    dax_name: "Scope 1 Emissions"
    dax_expression: "SUM(fact_sustainability[Scope1_Emissions])"
    lineage: ["fact_sustainability.Scope1_Emissions"]
    source_grain: "facility"
    source_column_ref: ["fact_sustainability.scope1_tons"]
    source_system: "Sustainability Platform"
    verified: true
  governance:
    business_owner: "Head of Sustainability"
    data_owner: "ESG BI"
    steward: "Environmental Analyst"
    review_cycle: "quarterly"
    validation_process: "manual review"
    qa_rules:
      - "No negative emissions values"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 0.98
    lineage_verified: true
    copilot_ready: true
```

## 3. Base Measures
```yaml
- kpi_key: "Total Energy (kWh)"
  kpi_type: "base"
  strategic_ref: "Renewable Energy Share %"
  impact_dimension: "ESG"
  domain_tag: ["Sustainability"]
  use_case_ref: ["ESG-002"]
  depends_on: []
  calc_type: amount
  refresh: monthly
  status: Active
  business:
    purpose: "Total electricity and heat consumption from all sources."
    definition: "Sum of electricity, heating, and fuel energy consumption."
    grain_scope: "Facility and energy meter level."
    unit_format: "kWh"
    interpretation: "Represents total energy demand."
  technical:
    dax_name: "Total Energy (kWh)"
    dax_expression: "SUM(fact_energy[Total Energy (kWh)])"
    lineage: ["fact_energy.Total_kWh"]
    source_grain: "facility"
    source_column_ref: ["fact_energy.total_kwh"]
    source_system: "Energy Management System"
    verified: true
  governance:
    business_owner: "Head of Sustainability"
    data_owner: "ESG BI"
    steward: "Energy Analyst"
    review_cycle: "quarterly"
    validation_process: "automated"
    qa_rules:
      - "Energy values must be > 0"
    version: "v2.0"
    last_review: "12.10.2025"
  metadata_quality:
    completeness_score: 1.00
    lineage_verified: true
    copilot_ready: true
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

_Last updated: 12.10.2025_
