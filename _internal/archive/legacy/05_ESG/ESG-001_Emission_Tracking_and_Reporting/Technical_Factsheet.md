# ESG-001 Emission Tracking and Reporting - Technical Factsheet

## 1. Data Contract (YAML)
Define tables, grain, keys, types.

`yaml
dimension:
  - name: dim_org
    grain: org
    columns:
      - {name: OrgID, type: text, role: primary_key}
      - {name: Region, type: text}
      - {name: Country, type: text}
      - {name: BusinessUnit, type: text}
  - name: dim_site
    grain: site
    columns:
      - {name: SiteID, type: text, role: primary_key}
      - {name: SiteName, type: text}
      - {name: SiteType, type: text}
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
  - name: dim_date
    grain: date
    columns:
      - {name: Date, type: date, role: primary_key}
  - name: dim_scope
    grain: emission_scope
    columns:
      - {name: ScopeCode, type: text, role: primary_key}
      - {name: ScopeName, type: text}
fact:
  - name: fact_sustainability
    grain: site_scope_month
    primary_key:
      - SiteID
      - ScopeCode
      - Month
    columns:
      - {name: SiteID, type: text, role: site_key, ref: dim_site}
      - {name: ScopeCode, type: text, role: scope_key, ref: dim_scope}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: Emission_tCO2e, type: decimal, role: amount}
      - {name: ActivityVolume, type: decimal, role: helper}
      - {name: EmissionFactor, type: decimal, role: helper}
      - {name: DataSource, type: text, role: attribute}
  - name: fact_financials
    grain: org_month
    primary_key:
      - OrgID
      - Month
    columns:
      - {name: OrgID, type: text, role: org_key, ref: dim_org}
      - {name: Month, type: date_key, ref: dim_date}
      - {name: NetSalesAmount, type: decimal, role: amount}
      - {name: ESGAlignedRevenueAmount, type: decimal, role: amount}
      - {name: CarbonPriceCost, type: decimal, role: amount}
relationships:
  - from: dim_site.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_sustainability.SiteID
    to: dim_site.SiteID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_sustainability.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
  - from: fact_sustainability.ScopeCode
    to: dim_scope.ScopeCode
    cardinality: many-to-one
    cross_filter: single
  - from: fact_financials.OrgID
    to: dim_org.OrgID
    cardinality: many-to-one
    cross_filter: single
  - from: fact_financials.Month
    to: dim_date.Date
    cardinality: many-to-one
    cross_filter: single
settings:
  timezone: Europe/Berlin
  fiscal_year_start: 01-01
`

## 2. Semantic Model Requirements
- Dataset: Contoso Sales Sample for Power BI Desktop.SemanticModel (ESG workspace) combining sustainability facts with finance for intensity calculations.
- Data ingestion from sustainability platform (Scopes 1-3) and ERP revenue tables; refresh monthly with mid-month provisional updates.
- Conformed org and date dimensions reused across clusters to support drill-through.
- Need calculation group or normalization table for emission factor versions to ensure transparency.
- Sort-by columns: CountrySort, ScopeOrder; maintain alphabetical fallback for sites.
- Hidden helper columns: ActivityVolume, EmissionFactor, DataSource for audit drill-through only.
- Hierarchies: Org Region > Country > Site; Scope hierarchy (Scope 1 > Stationary/Mobile, Scope 2 > Market/Location, Scope 3 categories).

## 3. Measures (DAX + Description)
`
Total CO2 Emissions (tCO2e) =
    // TODO: Provide DAX via Power BI MCP summing fact_sustainability[Emission_tCO2e]
`
Description:
  Purpose: Absolute emissions KPI.
  Definition: Sum of Emission_tCO2e respecting filters.
  Unit/Format: Decimal with 1 decimal.
  Lineage: fact_sustainability.
  QA: Reconcile vs sustainability platform export (variance <= 0.5 %).

`
Carbon Emission Intensity =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([Total CO2 Emissions (tCO2e)], [Net Sales Amount])
`
Description:
  Purpose: Normalized KPI.
  Definition: Emissions divided by Net Sales Amount using DIVIDE.
  Unit/Format: tCO2e per monetary unit (display as number with 4 decimals).
  Lineage: fact_sustainability, fact_financials.
  QA: Compare vs finance/ESG workbook; tolerance 0.5 %.

`
ESG-Aligned Revenue % =
    // TODO: Provide DAX via Power BI MCP using DIVIDE([ESG-Aligned Revenue Amount], [Net Sales Amount])
`
Description:
  Purpose: Shows taxonomy-aligned portfolio share.
  Definition: Aligned revenue divided by total revenue (DIVIDE).
  Unit/Format: Percentage 1 decimal.
  Lineage: fact_financials.
  QA: Must match taxonomy reporting pack.

`
Scope Mix % =
    // TODO: Provide DAX via Power BI MCP returning share of each scope within total emissions
`
Description:
  Purpose: Understand emission composition.
  Definition: Emissions per scope divided by total emissions.
  Unit/Format: Percentage 1 decimal.
  Lineage: fact_sustainability grouped by ScopeCode.
  QA: Validate each scope sums to 100 %.

`
Carbon Budget Variance (tCO2e) =
    // TODO: Provide DAX via Power BI MCP subtracting target budget from actual emissions (requires target table)
`
Description:
  Purpose: Show deviation vs reduction pathway.
  Definition: Actual emissions minus target emissions for selected period.
  Unit/Format: tCO2e (signed).
  Lineage: fact_sustainability + target table.
  QA: Align with sustainability roadmap file.

## 4. Defaults & Formatting
| Field | Setting | Notes |
|-------|---------|-------|
| Total CO2 Emissions (tCO2e) | Sum, Decimal 1 | Display folder: 01_Emissions |
| Carbon Emission Intensity | No summarization, Decimal 4 | Display folder: 01_Emissions |
| ESG-Aligned Revenue % | No summarization, Percentage 1 | Display folder: 02_Finance |
| Net Sales Amount | Sum, Currency 0 | Display folder: 02_Finance |
| Scope Mix % | No summarization, Percentage 1 | Display folder: 01_Emissions |
| Carbon Budget Variance | No summarization, Decimal 1 | Display folder: 01_Emissions |
| Geographic fields | Do not summarize | Provide Region > Country > Site hierarchy |

## 5. Visual Requirements (Technical)
| Visual | Purpose | Required Fields | Notes |
|--------|---------|-----------------|-------|
| KPI Cards | Headline status | Total Emissions, Intensity, ESG-Aligned Revenue %, Scope Mix | Include plan/target references |
| Line Chart | Trend over time | Date hierarchy, Total Emissions, Intensity | Rolling 24-36 months |
| Waterfall | Explain intensity variance | Variance drivers calculation table | Drivers: volume, mix, revenue, offsets |
| Map/Treemap | Hotspot identification | Region/Country/Site, Emissions | Use color scale by variance |
| Detail Table | Audit-ready data | Scope, Site, Emission factor, Data source | Include drill-through to evidence |

## 6. Performance & Refresh
- Storage mode: Import with incremental refresh (Month rolling 60M) due to long history; optional aggregated table for >5 years.
- Partition facts by Month; ensure sustainability API query folding using date filters.
- Refresh cadence: monthly official run (first business day) plus ad-hoc refresh after data corrections; finance table refreshed weekly.
- Monitor dataset size; consider aggregations for Scope 3 categories due to volume.

## 7. RLS/OLS Requirements
- Role ESG_Global: full access for sustainability team.
- Role Region_Manager: filter dim_org[Region] = allowed regions via security table.
- Role Site_Manager: filter dim_site[SiteID] list to restrict site view.
- OLS: hide ESG-Aligned Revenue Amount for non-finance roles if needed.

## 8. QA & Validation Rules
| Check Type | Object | Rule | Tolerance |
|------------|--------|------|-----------|
| Referential Integrity | fact_sustainability -> dim_site/dim_date/dim_scope | >= 99.9 % matches | 0.1 % |
| Scopes_Complete | fact_sustainability | All three scopes present per reporting period | 0 missing |
| Emissions_Reconcile | Total CO2 Emissions vs source | Variance <= 0.5 % | 0.5 % |
| Intensity_Within_Range | Carbon Emission Intensity | 0 <= intensity <= 5 tCO2e per monetary unit | Hard fail |
| ESG_Revenue_TieOut | ESG-Aligned revenue | Match taxonomy disclosure | +/- 0.2 % |
