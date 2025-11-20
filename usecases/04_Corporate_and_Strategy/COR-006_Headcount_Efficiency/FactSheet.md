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
expected_impact: "+2–3 % revenue per FTE; -1–2 pp personnel cost ratio."
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

# Headcount Efficiency & Revenue per FTE

## 1. Business Goal
Increase headcount efficiency by improving revenue and gross margin per FTE while controlling personnel cost ratio across business units and functions.

---

## 2. Business Context
Headcount and personnel costs are major components of operating expenses.  
Without a clear, comparable view of productivity across units and functions, organizations risk over- or understaffing and misaligned investments.  
This Use Case provides a standardized view of revenue per FTE, gross margin per FTE, and personnel cost ratio.

---

## 3. Key Questions
- How much revenue and gross margin do we generate per FTE across regions and functions?
- How does personnel cost ratio develop over time and by business unit?
- Where do we see over- or understaffing relative to output and strategic priorities?

---

## 4. Key KPIs
| KPI                   | Definition                          | Unit | Format   |
|-----------------------|-------------------------------------|------|----------|
| Revenue per FTE       | Net Sales Amount / FTE Count        | EUR  | € #,0.00 |
| Gross Margin per FTE  | Gross Margin Amount / FTE Count     | EUR  | € #,0.00 |
| Personnel Cost Ratio %| Personnel Cost Amount / Net Sales   | %    | 1 decimal|

---

## 5. Required Attributes (Business-Level)
- Org (region, country, business unit)
- Function/department
- FTE count and personnel cost per period
- Net sales and gross margin per org/period

---

## 6. Segmentation & Hierarchies
- Org: Region > Country > BusinessUnit  
- Function: Function > Department  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- FTE calculation (full-time equivalents) is consistent across units and documented.
- Personnel cost includes salary, bonuses, and benefits; overhead allocation rules are defined.

---

## 8. Data Freshness & Cadence
- HR and finance data: monthly.
- Reporting cadence: monthly and quarterly performance reviews.

---

## 9. Edge Cases & QA Rules
- Units with FTE Count = 0 but with revenue/costs are flagged.
- Personnel cost and FTE totals reconcile with HR and finance systems.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Headcount fact with FTE and personnel cost by org/function/month.
  - Financials fact with revenue and gross margin by org/month.

---

## 11. Typical Actions
| Action                                 | Code | Expected Effect              |
|----------------------------------------|------|------------------------------|
| Rebalance staffing across units        | E4   | Higher revenue per FTE       |
| Align hiring with productivity trends  | SP1  | More efficient headcount use |
| Optimize mix of roles and seniority    | O2   | Lower personnel cost ratio   |

---

## 12. Expected Business Impact
| Dimension    | Expected Impact            | Measurement   |
|--------------|----------------------------|---------------|
| Productivity | +2–3 % revenue per FTE    | vs baseline   |
| Cost         | -1–2 pp personnel cost ratio | vs baseline |

---

## 13. Related Processes
Workforce Planning → Budgeting → Performance & Reward → Strategic Workforce Management.

---

## 14. Insights & Learnings
Typical findings include functions with structurally lower productivity, and regions where headcount and revenue are misaligned.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-002 Workforce Productivity & Turnover Analysis](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[HR-002 Workforce Productivity](../HR-002_Workforce_Productivity/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

