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

# Investment & CapEx Tracking

## 1. Business Goal
Provide transparency on capital expenditures and investment projects across the portfolio and their impact on cash flow and strategic priorities.

---

## 2. Business Context
CapEx decisions shape the company’s future capacity and competitive position.  
Boards require a clear view on where capital is invested, how it compares to budget, and how it impacts cash flow.  
This Use Case standardizes CapEx tracking across projects and business units.

---

## 3. Key Questions
- How much are we investing (CapEx) by pillar, program, project, and business unit?
- How do actual CapEx and budget compare over time?
- How does CapEx relate to operating cash flow and strategic priorities?

---

## 4. Key KPIs
| KPI              | Definition                                       | Unit | Format   |
|------------------|--------------------------------------------------|------|----------|
| CapEx Amount     | Sum of capital expenditures in period           | EUR  | € #,0.00 |
| CapEx Ratio %    | CapEx Amount / Operating Cash Flow or Revenue   | %    | 1 decimal|
| Operating Cash Flow Amount | Cash generated from operations        | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- Org (region, country, business unit)
- Project (pillar, program, project name, status)
- CapEx actuals and budgets by period
- Operating cash flow by org/period

---

## 6. Segmentation & Hierarchies
- Org: Region > Country > BusinessUnit  
- Portfolio: Pillar > Program > Project  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- CapEx is defined according to accounting policy and tracked consistently in finance systems.
- Project hierarchy (pillar/program/project) is maintained and up to date.

---

## 8. Data Freshness & Cadence
- Data refresh: monthly (aligned with financial close).
- Reporting cadence: monthly and quarterly investment reviews.

---

## 9. Edge Cases & QA Rules
- Projects without a pillar/program assignment are flagged.
- CapEx totals reconcile with cash flow statement and balance sheet movements.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - CapEx fact with actuals and budgets by project and org.
  - Cash flow fact with operating cash flow by org.

---

## 11. Typical Actions
| Action                                  | Code | Expected Effect                    |
|-----------------------------------------|------|------------------------------------|
| Reprioritize investments in portfolio   | SP1  | Better alignment with strategy     |
| Adjust CapEx pace to cash generation    | SP2  | More stable liquidity              |
| Improve governance for CapEx overruns   | O2   | Fewer budget overruns             |

---

## 12. Expected Business Impact
| Dimension | Expected Impact                    | Measurement   |
|-----------|------------------------------------|---------------|
| Liquidity | Better CapEx vs cash alignment     | qualitative   |
| Strategy  | Higher share of CapEx in priority areas | portfolio view |

---

## 13. Related Processes
Strategic Planning → Investment Approval → CapEx Execution → Post-Investment Review.

---

## 14. Insights & Learnings
Typical findings include under- or over-investment in specific pillars, projects with repeated overruns, and misalignment between CapEx and cash generation.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-003 ESG & Compliance Monitoring](../COR-003_ESG_and_Compliance_Monitoring/FactSheet.md)`  

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
