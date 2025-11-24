# ESG & Compliance Monitoring - Technical Factsheet

## 1. Data Contract (YAML)
```yaml
facts:
- name: fact_esg_emissions
  grain: org_scope_month
  primary_key:
  - OrgID
  - Scope
  - Month
  required_columns:
  - name: OrgID
    type: string
    role: org_key
  - name: Scope
    type: string
    role: attribute
  - name: Month
    type: date
    role: date_key
  - name: EmissionTons
    type: decimal
    role: amount
  - name: EnergyConsumptionMWh
    type: decimal
    role: amount
- name: fact_esg_revenue
  grain: org_month
  primary_key:
  - OrgID
  - Month
  required_columns:
  - name: OrgID
    type: string
    role: org_key
  - name: Month
    type: date
    role: date_key
  - name: RevenueAmount
    type: decimal
    role: amount
  - name: AlignedRevenueAmount
    type: decimal
    role: amount
  - name: CapexAlignedAmount
    type: decimal
    role: amount
- name: fact_compliance_incidents
  grain: incident
  primary_key:
  - IncidentID
  required_columns:
  - name: IncidentDate
    type: date
    role: date_key
  - name: OrgID
    type: string
    role: org_key
  - name: Severity
    type: string
    role: attribute
  - name: Category
    type: string
    role: attribute
  - name: Status
    type: string
    role: status
  - name: ResolutionDate
    type: date
    role: helper
- name: fact_safety
  grain: site_month
  primary_key:
  - SiteID
  - Month
  required_columns:
  - name: HoursWorked
    type: decimal
    role: amount
  - name: LTIFRCount
    type: int
    role: count
dims:
- name: dim_org
  grain: org
  primary_key:
  - OrgID
  required_columns:
  - name: Region
    type: string
  - name: Country
    type: string
  - name: Site
    type: string
  - name: Industry
    type: string
- name: dim_date
  grain: date
  primary_key:
  - Date
relationships:
- from: fact_esg_emissions.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_esg_emissions.Month
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_esg_revenue.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_esg_revenue.Month
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_compliance_incidents.OrgID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
- from: fact_compliance_incidents.IncidentDate
  to: dim_date.Date
  cardinality: many-to-one
  direction: single
- from: fact_safety.SiteID
  to: dim_org.OrgID
  cardinality: many-to-one
  direction: single
```

## 2. Semantic Model Requirements
- Dataset Model: Contoso Sales Sample for Power BI Desktop.SemanticModel
- Required facts/dims per contract above.
- Ensure relationships are single-direction many-to-one (role-playing dates if needed).
- Provide conformed Org/Product/Initiative hierarchies.

## 3. Measures (DAX + Description)
Following KPIs require measures (DAX delivered separately):
- ESG-Aligned Revenue % (ID: esg.aligned_revenue.pct)
- Carbon Emission Intensity (ID: esg.carbon_intensity.tco2e_per_revenue)
- Total CO2 Emissions (ID: esg.co2.total.tco2e)
- Compliance Incidents Count (ID: gov.compliance.incidents.count)
- Lost Time Injury Frequency Rate (ID: esg.ltifr.rate)

## 4. Defaults & Formatting
- Apply correct format strings (currency, %, integer).
- Use display folders (01_Strategic, 02_Variance, etc.).
- Set data categories for Org/Initiative/Timeline fields.

## 5. Visual / Interaction Requirements
- Map visuals (cards, bridges, funnels) to required fields.
- Define drill paths for Org, Initiative, Time.
- Specify tooltip fields and sort-by logic.

## 6. Performance & Refresh
- Storage mode: Import (unless monthly snapshot suggests Hybrid).
- Refresh cadence aligned with corporate close cadence.
- Partitioning by FiscalPeriod where data volume is high.

## 7. RLS/OLS Requirements
- Org-based RLS (Region/Entity).
- Optional Initiative-based restrictions for project owners.

## 8. QA & Validation Rules
- RI_OK
- Emission_Positive
- Taxonomy_Share_100

## 9. Model Mapping Reference
- Emission Tons -> fact_esg_emissions[EmissionTons]
- Energy Consumption -> fact_esg_emissions[EnergyConsumptionMWh]
- Aligned Revenue Amount -> fact_esg_revenue[AlignedRevenueAmount]
- Total Revenue -> fact_esg_revenue[RevenueAmount]
- Capex Aligned Amount -> fact_esg_revenue[CapexAlignedAmount]
- Compliance Incident -> fact_compliance_incidents[IncidentID]
- Incident Severity -> fact_compliance_incidents[Severity]
- LTIFR Count -> fact_safety[LTIFRCount]
- Hours Worked -> fact_safety[HoursWorked]
- Org -> dim_org[OrgID]
- Date -> dim_date[Date]
