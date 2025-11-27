---
id: "COR-009"
title: "Investment & CapEx Tracking"
domain: "Corporate and Strategy"
owner: "CFO / Head of Corporate Finance"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Investment & CapEx Ratio %", "Free Cash Flow"]
supports_strategic_kpi_ids: ["fin.liquidity.capex_ratio.pct", "fin.liquidity.operating_cash_flow"]
action_codes: ["SP1", "SP2", "O2"]
expected_impact: "Better alignment of CapEx with strategy; improved visibility into investment pipeline and cash impact."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>BusinessUnit",
  "Portfolio.Pillar>Program>Project",
  "Capex.Category",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 24M",
  "Org: All",
  "Capex Category: All"
]
qa_asserts: ["RI_OK", "Capex_vs_Budget_Reconciles", "Project_Status_Tracked"]
required_kpi_ids: [
  "fin.liquidity.capex.amount",
  "fin.liquidity.capex_ratio.pct",
  "fin.liquidity.operating_cash_flow"
]
required_kpis:
  fin.liquidity.capex.amount: "CapEx Amount"
  fin.liquidity.capex_ratio.pct: "CapEx Ratio %"
  fin.liquidity.operating_cash_flow: "Operating Cash Flow Amount"
data_requirements:
  facts:
    - name: fact_capex
      grain: project_period
      primary_key: [ProjectID, Period]
      required_columns:
        - { name: ProjectID, type: string, role: attribute }
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Capex Category", type: string, role: attribute }
        - { name: "Capex Actual Amount", type: decimal, role: amount }
        - { name: "Capex Budget Amount", type: decimal, role: amount }
    - name: fact_cashflow
      grain: org_period
      primary_key: [OrgID, Period]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Period, type: date, role: date_key }
        - { name: "Operating Cash Flow Amount", type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_project
      grain: project
      primary_key: [ProjectID]
      required_columns:
        - { name: Pillar, type: string }
        - { name: Program, type: string }
        - { name: ProjectName, type: string }
        - { name: Status, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Quarter, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_capex.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_capex.ProjectID, to: dim_project.ProjectID, cardinality: many-to-one, direction: single }
    - { from: fact_capex.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_cashflow.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_cashflow.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Capex Actual Amount": "fact_capex[Capex Actual Amount]"
  "Capex Budget Amount": "fact_capex[Capex Budget Amount]"
  "Capex Category": "fact_capex[Capex Category]"
  "Operating Cash Flow Amount": "fact_cashflow[Operating Cash Flow Amount]"
  "Org": "dim_org[OrgID]"
  "Project": "dim_project[ProjectID]"
  "Date": "dim_date[Date]"
---

# Investment & CapEx Tracking - Business Factsheet

## 1. Summary
- **Business Goal:** Provide transparency on capital expenditures and investment projects across the portfolio and their impact on cash flow and strategic priorities.

---
- **Target Audience:** CFO / Head of Corporate Finance
- **Business Priority:** High
- **Expected Impact:** Better alignment of CapEx with strategy; improved visibility into investment pipeline and cash impact.

## 2. Core Questions
- How much are we investing (CapEx) by pillar, program, project, and business unit?
- How do actual CapEx and budget compare over time?
- How does CapEx relate to operating cash flow and strategic priorities?
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
- KPI cards for CapEx Amount, CapEx Ratio %, Operating Cash Flow Amount with Plan/LY deltas.
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