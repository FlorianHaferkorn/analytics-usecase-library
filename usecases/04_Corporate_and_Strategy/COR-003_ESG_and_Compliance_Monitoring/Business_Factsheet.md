---
id: "COR-003"
title: "ESG & Compliance Monitoring"
domain: "Corporate and Strategy"
owner: "Head of Sustainability / Compliance Office"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["ESG-Aligned Revenue %", "Carbon Emission Intensity", "Compliance Incidents Count"]
supports_strategic_kpi_ids: ["esg.aligned_revenue.pct", "esg.carbon_intensity.tco2e_per_revenue", "gov.compliance.incidents.count"]
action_codes: ["PC2", "C4", "O2", "O3", "SP1"]
expected_impact: "+10-20 % rating improvement; -10-15 % Scope 1-2 emissions; -30 % incident frequency"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Site",
  "ESG.Dimension>E/S/G",
  "Emission.Scope>Scope1>Scope2>Scope3",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "ESG Dimension: All"
]
qa_asserts: ["RI_OK", "Emission_Positive", "Taxonomy_Share_100"]
required_kpi_ids: [
  "esg.aligned_revenue.pct",
  "esg.carbon_intensity.tco2e_per_revenue",
  "esg.co2.total.tco2e",
  "gov.compliance.incidents.count",
  "esg.ltifr.rate"
]
required_kpis:
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  esg.carbon_intensity.tco2e_per_revenue: "Carbon Emission Intensity"
  esg.co2.total.tco2e: "Total CO2 Emissions"
  gov.compliance.incidents.count: "Compliance Incidents Count"
  esg.ltifr.rate: "Lost Time Injury Frequency Rate"
data_requirements:
  facts:
    - name: fact_esg_emissions
      grain: org_scope_month
      primary_key: [OrgID, Scope, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Scope, type: string, role: attribute }
        - { name: Month, type: date, role: date_key }
        - { name: EmissionTons, type: decimal, role: amount }
        - { name: EnergyConsumptionMWh, type: decimal, role: amount }
    - name: fact_esg_revenue
      grain: org_month
      primary_key: [OrgID, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: RevenueAmount, type: decimal, role: amount }
        - { name: AlignedRevenueAmount, type: decimal, role: amount }
        - { name: CapexAlignedAmount, type: decimal, role: amount }
    - name: fact_compliance_incidents
      grain: incident
      primary_key: [IncidentID]
      required_columns:
        - { name: IncidentDate, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: Severity, type: string, role: attribute }
        - { name: Category, type: string, role: attribute }
        - { name: Status, type: string, role: status }
        - { name: ResolutionDate, type: date, role: helper }
    - name: fact_safety
      grain: site_month
      primary_key: [SiteID, Month]
      required_columns:
        - { name: HoursWorked, type: decimal, role: amount }
        - { name: LTIFRCount, type: int, role: count }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: Site, type: string }
        - { name: Industry, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_esg_emissions.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_esg_emissions.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_esg_revenue.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_esg_revenue.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_compliance_incidents.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_compliance_incidents.IncidentDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_safety.SiteID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
model_mapping:
  "Emission Tons": "fact_esg_emissions[EmissionTons]"
  "Energy Consumption": "fact_esg_emissions[EnergyConsumptionMWh]"
  "Aligned Revenue Amount": "fact_esg_revenue[AlignedRevenueAmount]"
  "Total Revenue": "fact_esg_revenue[RevenueAmount]"
  "Capex Aligned Amount": "fact_esg_revenue[CapexAlignedAmount]"
  "Compliance Incident": "fact_compliance_incidents[IncidentID]"
  "Incident Severity": "fact_compliance_incidents[Severity]"
  "LTIFR Count": "fact_safety[LTIFRCount]"
  "Hours Worked": "fact_safety[HoursWorked]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# ESG & Compliance Monitoring - Business Factsheet

## 1. Summary
- **Business Goal:** Integrate Environmental, Social, and Governance (ESG) metrics into business performance management to ensure transparency, regulatory compliance, and sustainable value creation.

---
- **Target Audience:** Head of Sustainability / Compliance Office
- **Business Priority:** High
- **Expected Impact:** +10-20 % rating improvement; -10-15 % Scope 1-2 emissions; -30 % incident frequency

## 2. Core Questions
- How do we perform against ESG and compliance KPIs (environmental, social, governance)?
- Are we on track for CSRD and EU taxonomy disclosure requirements?
- Which entities or sites pose compliance or sustainability risks?
- What share of revenue and investments are taxonomy-aligned?
- How do ESG improvements correlate with financial performance?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for ESG-Aligned Revenue %, Carbon Emission Intensity, Total CO2 Emissions, Compliance Incidents Count, Lost Time Injury Frequency Rate with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a