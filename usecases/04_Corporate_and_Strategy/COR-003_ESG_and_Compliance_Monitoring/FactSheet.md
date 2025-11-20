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

# ESG & Compliance Monitoring

## 1. Business Goal
Integrate Environmental, Social, and Governance (ESG) metrics into business performance management to ensure transparency, regulatory compliance, and sustainable value creation.

---

## 2. Business Context
Regulators, investors, and customers demand auditable ESG disclosures (e.g., CSRD, EU Taxonomy). Data is scattered across facilities, finance, and compliance tools, making it hard to track progress or respond to incidents quickly. This use case unifies environmental, social, and governance KPIs with financial context so leadership can prioritize decarbonization, monitor safety and ethics, and tie ESG achievements to value creation.

---

## 3. Key Questions
- How do we perform against ESG and compliance KPIs (environmental, social, governance)?
- Are we on track for CSRD and EU taxonomy disclosure requirements?
- Which entities or sites pose compliance or sustainability risks?
- What share of revenue and investments are taxonomy-aligned?
- How do ESG improvements correlate with financial performance?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| ESG-Aligned Revenue % | Taxonomy-aligned revenue / Total revenue | % | 1 decimal |
| Carbon Emission Intensity | Total CO2e / Revenue | tCO2e/EUR | 2 decimals |
| Total CO2 Emissions | Scope 1+2 (+Scope 3 optional) | tCO2e | 0 decimals |
| Compliance Incidents Count | Number of incidents per period | count | integer |
| LTIFR | Lost time injuries / 1M hours worked | rate | 2 decimals |

---

## 5. Required Attributes (Business-Level)
- Org (legal entity, plant, region)
- Date (month or quarter end)
- Energy Consumption, CO2 Emissions (Scope 1-3)
- Revenue, Headcount, Hours Worked
- Incident Type, Severity, Resolution Date
- Optional: Supplier, Project, ESG Category (E/S/G), Certification Level

---

## 6. Segmentation & Hierarchies
- Org: Region > Country > Site
- ESG Dimension: Environment / Social / Governance
- Emission Scope: Scope 1 > Scope 2 > Scope 3 Category
- Compliance: Policy Area > Severity > Status
- Time: Year > Quarter > Month

---

## 7. Scope & Assumptions
- CO2 conversion factors based on GHG Protocol.
- Scope 1 = direct emissions, Scope 2 = purchased energy, Scope 3 = value chain.
- ESG-aligned revenue calculated per EU Taxonomy.
- Compliance incidents recorded post-validation by Legal/Compliance.
- Data aggregated monthly; restated quarterly for audit consistency.

---

## 8. Data Freshness & Cadence
- Emission and energy data refresh monthly (automated upload) with sensor feeds available daily for high-impact sites.
- Compliance and safety incidents ingested daily after approval.
- Revenue alignment re-calculated each quarter after financial close.
- Data Owner: Sustainability Office (E), HR Safety (S), Compliance (G); Technical Owner: Corporate BI.

---

## 9. Edge Cases & QA Rules
- Emissions cannot be negative.
- ESG-Aligned Revenue % must not exceed 100 %.
- Incident records must include resolution date.
- Referential integrity >= 99.9 % across Date/Org/Category.
- All metrics documented with source and methodology (audit trail).

---

## 10. Minimum Viable Dataset (MVD)
- Required: CO2/energy by site-scope, revenue totals, compliance incident log.
- Optional: Scope 3 categories, taxonomy CapEx/OpEx share, safety hours.
- Extended: Supplier ESG scores, external ratings, carbon pricing scenarios.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Implement energy efficiency initiatives and green sourcing | PC2 | CO2 -10-20 %; cost savings improve |
| Increase workforce diversity and inclusion programs | C4 | Diversity improves; engagement improves |
| Strengthen safety programs in high-risk sites | O2 | LTIFR -30 % |
| Automate ESG data collection and validation workflows | O3 | Reporting latency reduces; audit reliability improves |
| Align sustainability KPIs with executive compensation | SP1 | Accountability improves; ESG target compliance improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Decarbonization | -10-15 % Scope 1-2 emissions | vs Prior Year |
| Compliance | -30 % incident frequency | vs baseline |
| Disclosure Quality | +10-20 % external rating improvement | ESG rating agency |

---

## 13. Related Processes
Sustainability Reporting -> Risk & Compliance Management -> Audit & Assurance -> Supplier Assessment -> Corporate Governance.

---

## 14. Insights & Learnings
Facilities with automated meter readings close their carbon books 3x faster and report 20 % fewer manual adjustments. Linking incident remediation to investment approvals accelerates root-cause fixes and improves regulator confidence.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_
