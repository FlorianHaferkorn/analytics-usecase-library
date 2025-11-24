---
id: "COR-004"
title: "Strategic KPI Dashboard (Enterprise Performance Overview)"
domain: "Corporate and Strategy"
owner: "Executive Board / Strategy Office"
impact: "Very High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Cash Conversion Cycle", "ESG-Aligned Revenue %", "Turnover %", "Project ROI %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days", "esg.aligned_revenue.pct", "hr.turnover.pct", "corp.project.roi.pct"]
action_codes: ["SP2", "O2", "SP1", "O3", "SP3"]
expected_impact: "Unified view of top KPIs; -50 % latency from data to decision; +100 % KPI-goal linkage"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "KPI.Domain>Sub-Domain",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Domain: All",
  "Org: All"
]
qa_asserts: ["RI_OK", "KPI_Source_Registered", "Plan_Actual_Alignment"]
required_kpi_ids: [
  "sales.net_sales.delta_pct.ly",
  "margin.gm.pct",
  "ops.working_capital.ccc.days",
  "hr.turnover.pct",
  "esg.aligned_revenue.pct",
  "corp.project.roi.pct"
]
required_kpis:
  sales.net_sales.delta_pct.ly: "Δ% Net Sales"
  margin.gm.pct: "Gross Margin %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
  hr.turnover.pct: "Turnover Rate %"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  corp.project.roi.pct: "Project ROI %"
data_requirements:
  facts:
    - name: fact_kpi_scores
      grain: kpi_org_month
      primary_key: [KpiID, OrgID, Month]
      required_columns:
        - { name: KpiID, type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: Domain, type: string, role: attribute }
        - { name: ActualValue, type: decimal, role: amount }
        - { name: PlanValue, type: decimal, role: amount }
        - { name: TargetValue, type: decimal, role: amount }
        - { name: Status, type: string, role: status }
        - { name: Owner, type: string, role: attribute }
        - { name: Commentary, type: string, role: text }
    - name: fact_initiatives
      grain: initiative
      primary_key: [InitiativeID]
      required_columns:
        - { name: InitiativeName, type: string, role: attribute }
        - { name: LinkedKpiID, type: string, role: attribute }
        - { name: Status, type: string, role: status }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
    - name: dim_kpi
      grain: kpi
      primary_key: [KpiID]
      required_columns:
        - { name: KPIName, type: string }
        - { name: Domain, type: string }
        - { name: SourceUseCase, type: string }
        - { name: Frequency, type: string }
  relationships:
    - { from: fact_kpi_scores.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_kpi_scores.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_kpi_scores.KpiID, to: dim_kpi.KpiID, cardinality: many-to-one, direction: single }
    - { from: fact_initiatives.LinkedKpiID, to: dim_kpi.KpiID, cardinality: many-to-one, direction: single }
model_mapping:
  "Actual Value": "fact_kpi_scores[ActualValue]"
  "Plan Value": "fact_kpi_scores[PlanValue]"
  "Target Value": "fact_kpi_scores[TargetValue]"
  "Status": "fact_kpi_scores[Status]"
  "Owner": "fact_kpi_scores[Owner]"
  "Commentary": "fact_kpi_scores[Commentary]"
  "KPI Name": "dim_kpi[KPIName]"
  "Domain": "dim_kpi[Domain]"
  "Source Use Case": "dim_kpi[SourceUseCase]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Strategic KPI Dashboard (Enterprise Performance Overview)

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
