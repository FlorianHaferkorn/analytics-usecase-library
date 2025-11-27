---
id: "ESG-001"
title: "Emission Tracking & Reporting"
domain: "ESG"
owner: "Head of Sustainability / ESG Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Carbon Emission Intensity", "ESG-Aligned Revenue %"]
supports_strategic_kpi_ids: ["esg.carbon_intensity.tco2e_per_revenue", "esg.aligned_revenue.pct"]
action_codes: ["E1", "S1"]
expected_impact: "-10 % Carbon Intensity, erhÃƒÂ¶hte Transparenz fÃƒÂ¼r regulatorische Reports."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Site",
  "Emission.Scope>Source",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Scope: 1-3",
  "Site: All"
]
qa_asserts: ["RI_OK", "Scopes_Complete", "Emissions_Reconcile"]
required_kpi_ids: [
  "esg.co2.total.tco2e",
  "esg.carbon_intensity.tco2e_per_revenue",
  "esg.aligned_revenue.pct"
]
required_kpis:
  esg.co2.total.tco2e: "Total CO2 Emissions (tCO2e)"
  esg.carbon_intensity.tco2e_per_revenue: "Carbon Emission Intensity"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
data_requirements:
  facts:
    - name: fact_sustainability
      grain: facility_month
      primary_key: [SiteID, Month]
      required_columns:
        - { name: SiteID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: Scope, type: string, role: attribute }
        - { name: Emission_tCO2e, type: decimal, role: amount }
    - name: fact_sales
      grain: org_month
      primary_key: [OrgID, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: NetSalesAmount, type: decimal, role: amount }
        - { name: ESGAlignedRevenueAmount, type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
    - name: dim_site
      grain: site
      primary_key: [SiteID]
      required_columns:
        - { name: SiteName, type: string }
        - { name: SiteType, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_sustainability.SiteID, to: dim_site.SiteID, cardinality: many-to-one, direction: single }
    - { from: fact_sustainability.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_sales.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_sales.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Total CO2 Emissions": "fact_sustainability[Emission_tCO2e]"
  "Net Sales Amount": "fact_sales[NetSalesAmount]"
  "ESG-Aligned Revenue Amount": "fact_sales[ESGAlignedRevenueAmount]"
---

# ESG-001 Emission Tracking and Reporting - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a single source of truth for Scopes 1-3 emissions and carbon intensity to meet regulatory reporting, investor transparency, and internal reduction targets.
- **Target Audience:** Chief Sustainability Officer, ESG Controlling, Finance, Operations leaders.
- **Business Priority:** High; required for CSRD/SEC reporting and corporate decarbonization roadmap.
- **Expected Impact:** -10 % carbon intensity plus faster audit-ready reporting (cycle time cut from weeks to days).

## 2. Core Questions
- How do absolute emissions (tCO2e) trend by scope, region, country, and site?
- What drives carbon intensity changes versus plan (activity volume, energy mix, offsets)?
- How much revenue qualifies as ESG-aligned and how does it evolve versus targets?
- Which sites or scopes require immediate abatement actions to stay on reduction trajectories?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Total CO2 Emissions (tCO2e) | Primary volume metric for greenhouse gases. | Aggregated tCO2e per scope/site/month from verified data. | Upward trend indicates need for mitigation; is compared to science-based targets. | Determines CAPEX allocation for abatement projects. |
| Carbon Emission Intensity | Normalizes emissions vs revenue for comparability. | tCO2e divided by net revenue (business description, no DAX). | Allows benchmarking against peers; target defined per industry. | Used in investor communication and internal incentives. |
| ESG-Aligned Revenue % | Shows portion of revenue meeting taxonomy/sustainability definitions. | Revenue tagged as taxonomy-aligned / total revenue. | Higher percentage demonstrates sustainable portfolio shift. | Supports strategic capital allocation and disclosures. |
| Scope 1 vs 2 vs 3 Mix | Highlights where emissions originate. | Share of total emissions per scope category. | Scope 3 often dominant; helps focus supplier engagement. | Drives supplier programs and renewable energy sourcing. |

## 4. Business Logic & Thresholds
- Emissions calculated with latest emission factors; factor changes documented with effective date.
- Intensity targets defined per year; >5 % deviation triggers action code S1 (strategic program review).
- ESG-aligned revenue must pass taxonomy eligibility and alignment tests; missing classification flagged as data issue.
- Automation ensures CSRD/SEC-ready exports with traceable audit trail; manual overrides require approval by ESG Controlling.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| E1 | Emission Reduction Sprint | Deploy technical/operational measures (fuel switch, efficiency upgrades) for high-emitting sites. | Scope/site exceeds pathway or carbon price threshold. | -5 to -10 % emissions for targeted site within 12 months. |
| S1 | Strategy and Portfolio Review | Rebalance portfolio, accelerate ESG-aligned offerings, update targets. | Carbon intensity misses target by >5 % for 2 quarters or ESG-aligned revenue stagnates. | Intensity back on track, ESG-aligned revenue +2 pp. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Total Emissions, Carbon Intensity, Scope mix, ESG-Aligned Revenue % versus target/plan.
- Alert banner for regulatory breaches or sites above carbon budget.

### 6.2 30-Second Layer (Story)
- Trend lines (12-24 months) for total emissions and intensity with target overlays.
- Waterfall explaining intensity variance (volume, mix, offsets, revenue).
- Geographic map/treemap highlighting hotspot regions/sites.

### 6.3 300-Second Layer (Detail)
- Drillable table Scope > Region > Site with KPI breakdown and action code status.
- Activity-based view (fuel, process, logistics) linking to abatement levers.
- Export-ready CSRD/SEC disclosure table with units (tCO2e, intensity, methodology notes).

## 7. Dependencies & Constraints
- Requires verified data from sustainability platform, energy management systems, and finance (revenue) with consistent org and date keys.
- Scope 3 categories must align with GHG Protocol; data freshness weekly for operational steering, monthly for formal reporting.
- Methodology metadata (emission factors, boundaries) stored in governance catalog and versioned.
- Sign-off workflow integrates with Legal/Compliance before external disclosure.

## 8. Success Criteria
- Leading: 95 % of sites submit data within 5 working days of period end; dashboard adoption by ESG Controlling weekly.
- Lagging: -10 % carbon intensity vs baseline and timely CSRD/SEC filings with zero audit findings.