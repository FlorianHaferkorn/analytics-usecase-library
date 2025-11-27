---
id: "COR-006"
title: "Headcount Efficiency & Revenue per FTE"
domain: "Corporate and Strategy"
owner: "Head of HR Controlling / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Headcount Efficiency %", "Revenue per FTE"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "hr.personnel_cost_ratio.pct"]
action_codes: ["E4", "SP1", "O2"]
expected_impact: "+2â€“3 % revenue per FTE; -1â€“2 pp personnel cost ratio."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>BusinessUnit",
  "Workforce.Function>Department",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Function: All"
]
qa_asserts: ["RI_OK", "Headcount_Positive", "FTE_Calculation_Consistent"]
required_kpi_ids: [
  "hr.revenue_per_fte.amount",
  "hr.personnel_cost_ratio.pct",
  "hr.gm_per_fte.amount"
]
required_kpis:
  hr.revenue_per_fte.amount: "Revenue per FTE"
  hr.personnel_cost_ratio.pct: "Personnel Cost Ratio %"
  hr.gm_per_fte.amount: "Gross Margin per FTE"
data_requirements:
  facts:
    - name: fact_headcount
      grain: org_function_month
      primary_key: [OrgID, FunctionID, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: FunctionID, type: string, role: attribute }
        - { name: Month, type: date, role: date_key }
        - { name: "FTE Count", type: decimal, role: helper }
        - { name: "Personnel Cost Amount", type: decimal, role: amount }
    - name: fact_financials
      grain: org_month
      primary_key: [OrgID, Month]
      required_columns:
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "Gross Margin Amount", type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_function
      grain: function
      primary_key: [FunctionID]
      required_columns:
        - { name: FunctionName, type: string }
        - { name: Department, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_headcount.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_headcount.FunctionID, to: dim_function.FunctionID, cardinality: many-to-one, direction: single }
    - { from: fact_headcount.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_financials.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_financials.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "FTE Count": "fact_headcount[FTE Count]"
  "Personnel Cost Amount": "fact_headcount[Personnel Cost Amount]"
  "Net Sales Amount": "fact_financials[Net Sales Amount]"
  "Gross Margin Amount": "fact_financials[Gross Margin Amount]"
  "Org": "dim_org[OrgID]"
  "Function": "dim_function[FunctionID]"
  "Date": "dim_date[Date]"
---

# Headcount Efficiency & Revenue per FTE - Business Factsheet

## 1. Summary
- **Business Goal:** Increase headcount efficiency by improving revenue and gross margin per FTE while controlling personnel cost ratio across business units and functions.

---
- **Target Audience:** Head of HR Controlling / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** +2"3 % revenue per FTE; -1"2 pp personnel cost ratio.

## 2. Core Questions
- How much revenue and gross margin do we generate per FTE across regions and functions?
- How does personnel cost ratio develop over time and by business unit?
- Where do we see over- or understaffing relative to output and strategic priorities?
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
- KPI cards for Revenue per FTE, Personnel Cost Ratio %, Gross Margin per FTE with Plan/LY deltas.
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