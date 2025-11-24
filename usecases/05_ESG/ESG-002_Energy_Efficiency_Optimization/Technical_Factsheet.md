# ESG-002 Energy Efficiency Optimization - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_site
    grain: site
    columns:
      - {name: SiteID, type: text, role: primary_key}
      - {name: SiteName, type: text}
      - {name: SiteType, type: text}
      - {name: Region, type: text}
      - {name: Country, type: text}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
  - name: dim_energy_source
    grain: energy_source
    columns:
      - {name: SourceCode, type: text, role: primary_key}
      - {name: SourceName, type: text}
      - {name: IsRenewable, type: boolean}
fact:
  - name: fact_energy
    grain: site_source_month
    primary_key:
      - SiteID
      - SourceCode
      - Month
    columns:
      - {name: SiteID, type: text, role: site_key, ref: dim_site}
      - {name: SourceCode, type: text, role: source_key, ref: dim_energy_source}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: Energy_kWh, type: decimal, role: amount}
      - {name: Renewable_kWh, type: decimal, role: amount}
      - {name: EnergyCostAmount, type: decimal, role: amount}
      - {name: ProductionOutput, type: decimal, role: helper}
  - name: fact_emissions
    grain: site_month
    primary_key:
      - SiteID
      - Month
    columns:
      - {name: SiteID, type: text, role: site_key, ref: dim_site}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: EnergyEmission_tCO2e, type: decimal, role: amount}
relationships:
  - from: fact_energy.SiteID
    to: dim_site.SiteID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_energy.SourceCode
    to: dim_energy_source.SourceCode
    cardinality: many-to-one
    cross_filter: single
  - from: fact_energy.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_emissions.SiteID
    to: dim_site.SiteID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_emissions.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Dataset shares dim_site and dim_date with ESG-001 for consistency; energy sources stored in dedicated dimension with renewable flag.
- Energy data ingested from BMS/IoT systems aggregated to monthly grain; maintain hourly detail in data lake but not in model.
- Production output optional but recommended for intensity calculations; align across operations systems.
- Relationship directions single; no bidirectional filters to avoid ambiguity between site and source contexts.
- Hidden helper columns: ProductionOutput, energy tariffs, meter IDs for troubleshooting.
- Hierarchies: Region > Country > Site; Source grouping (Electricity, Gas, Steam, Renewable Onsite/Offsite).

## 3. Measures (DAX + Description)
`
Total Energy (kWh) =
    // TODO: Provide DAX via Power BI MCP summing fact_energy[Energy_kWh]
`
Description:
  Purpose: Absolute consumption.
  Definition: Sum of Energy_kWh respecting filters.
  Unit/Format: Decimal (0 decimals).
  Lineage: fact_energy.
  QA: Reconcile vs metering export (variance <= 0.5 %).

`
Renewable Energy (kWh) =
    // TODO: Provide DAX via Power BI MCP summing fact_energy[Renewable_kWh]
`
Description:
  Purpose: Renewable volume.
  Definition: Sum of Renewable_kWh (ensures <= Total Energy).
  Unit/Format: Decimal.
  Lineage: fact_energy.
  QA: Validate classification vs sustainability dataset.

`
Renewable Share % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Renewable Energy (kWh)], [Total Energy (kWh)])
`
Description:
  Purpose: KPI for energy mix.
  Definition: Renewable energy divided by total energy.
  Unit/Format: Percentage 1 decimal.
  Lineage: measures above.
  QA: Must stay between 0 and 100 %.

`
Energy Cost Amount =
    // TODO: Provide DAX via Power BI MCP summing fact_energy[EnergyCostAmount]
`
Description:
  Purpose: Monetary exposure.
  Definition: Sum of EnergyCostAmount.
  Unit/Format: Currency 0.
  Lineage: fact_energy.
  QA: Tie-out with finance energy ledger (variance <= 1 %).

`
Energy Intensity (kWh per Output) =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Total Energy (kWh)], [Production Output])
`
Description:
  Purpose: Efficiency indicator.
  Definition: Energy per production unit (if production data available) or per revenue.
  Unit/Format: Decimal 2.
  Lineage: fact_energy[Energy_kWh], ProductionOutput.
  QA: Validate vs operations KPI.

`
Energy Emission Intensity =
    // TODO: Provide DAX via Power BI MCP dividing fact_emissions[EnergyEmission_tCO2e] by [Production Output] or revenue
`
Description:
  Purpose: Link to ESG KPIs.
  Definition: Emissions from energy / production output (or revenue).
  Unit/Format: Decimal 3.
  Lineage: fact_emissions.
  QA: Align with ESG-001 intensity.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Total Energy (kWh) | Sum, Decimal 0 | Display folder: 01_Energy |
| Renewable Energy (kWh) | Sum, Decimal 0 | Display folder: 01_Energy |
| Renewable Share % | No summarization, Percentage 1 | Display folder: 01_Energy |
| Energy Cost Amount | Sum, Currency 0 | Display folder: 02_Cost |
| Energy Intensity | No summarization, Decimal 2 | Display folder: 01_Energy |
| Energy Emission Intensity | No summarization, Decimal 3 | Display folder: 01_Energy |
| Site hierarchy fields | Do not summarize | Provide Region > Country > Site |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline metrics | Total Energy, Renewable Share %, Energy Cost Amount, Energy Intensity | Include plan/target references |
| Trend Line | Monitor KPIs | Date hierarchy, energy measures | Rolling 24 months |
| Heatmap / Matrix | Compare sites | Region/Country/Site, Renewable Share %, Energy Intensity | Conditional formatting for thresholds |
| Waterfall | Cost variance analysis | Custom calculation table driven by volume/rate/mix | Align with finance view |
| Detail Table | Project tracker | Site, Source, KPIs, Action Codes, Payback months | Include drill-through to meter readings |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh (Month rolling 36M) to balance history and performance; keep detailed telemetry outside dataset.
- Partition by Month and Source to optimize refresh; ensure query folding via parameterized filters.
- Refresh nightly for active sites, weekly for long-tail; manual refresh allowed after energy audits.
- Monitor dataset size; consider aggregations for long history or implement dataflow pre-aggregation.

## 7. RLS/OLS Requirements
- Role Energy_Global: unrestricted.
- Role Region_Ops: filter dim_site[Region] using security mapping.
- Role Site_Manager: restrict to specific SiteIDs.
- Optional OLS to hide cost amounts for non-finance roles while allowing energy volume access.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_energy -> dim_site/dim_date/dim_energy_source | >= 99.7 % match | 0.3 % |
| Energy_Reconcile | Total Energy vs BMS export | Variance <= 0.5 % | 0.5 % |
| Renewable_Share_Bounds | Renewable Share % | KPI must remain within 0-100 % | Hard fail |
| Intensity_Within_Range | Energy intensity | Must be positive; extreme values flagged | Hard fail |
| Cost_vs_Finance | Energy Cost Amount | Align with finance ledger | +/- 1 % |
