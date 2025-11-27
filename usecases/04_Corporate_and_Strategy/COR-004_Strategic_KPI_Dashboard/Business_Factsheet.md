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
  sales.net_sales.delta_pct.ly: "Î”% Net Sales"
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

# Strategic KPI Dashboard (Enterprise Performance Overview) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a single, consolidated view of strategic KPIs across all business domains - enabling leadership to monitor execution of corporate strategy, track key objectives, and steer actions based on real-time insights.

---
- **Target Audience:** Executive Board / Strategy Office
- **Business Priority:** Very High
- **Expected Impact:** Unified view of top KPIs; -50 % latency from data to decision; +100 % KPI-goal linkage

## 2. Core Questions
- Are we on track to achieve corporate strategic and financial targets?
- Which business domains drive value creation or risk?
- How do operational, financial, and ESG metrics correlate?
- Where are emerging risks or opportunities across the portfolio?
- What trends require strategic intervention?
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
- KPI cards for ÃŽâ€% Net Sales, Gross Margin %, Cash Conversion Cycle (Days), Turnover Rate %, ESG-Aligned Revenue % with Plan/LY deltas.
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