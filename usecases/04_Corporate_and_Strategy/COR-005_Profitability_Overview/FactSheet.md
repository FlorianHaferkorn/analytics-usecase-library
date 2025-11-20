---
id: "COR-005"
title: "Profitability Overview (EBITDA & Net Margin)"
domain: "Corporate and Strategy"
owner: "CFO / Head of Controlling"
impact: "Very High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Revenue Growth %", "EBITDA Margin %", "Gross Margin %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.ebitda.pct", "margin.gm.pct"]
action_codes: ["SP1", "SP2", "O2"]
expected_impact: "Unified view on profitability from gross margin to EBITDA and net margin; faster, more aligned steering."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "P&L.Line>Sub-Line",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 24M",
  "Org: All"
]
qa_asserts: ["RI_OK", "P&L_Reconciles", "GrossMargin_Consistent"]
required_kpi_ids: [
  "sales.net_sales.amount",
  "cost.cogs.amount",
  "profit.ebitda_margin"
]
required_kpis:
  sales.net_sales.amount: "Net Sales Amount"
  cost.cogs.amount: "COGS Amount"
  profit.ebitda_margin: "EBITDA Margin %"
data_requirements:
  facts:
    - name: fact_pnl
      grain: org_period_pnl
      primary_key: [OrgID, Period, PnLLine]
      required_columns:
        - { name: Period, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: PnLLine, type: string, role: attribute }
        - { name: "Amount", type: decimal, role: amount }
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
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_pnl.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_pnl.Period, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "PnL Amount": "fact_pnl[Amount]"
  "PnL Line": "fact_pnl[PnLLine]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Profitability Overview (EBITDA & Net Margin)

## 1. Business Goal
Provide a single, consolidated profitability view from revenue and gross margin down to EBITDA and net margin, enabling aligned discussion in management and board steering.

---

## 2. Business Context
Finance and business functions often work with multiple versions of profitability views (P&L, management reporting, dashboards).  
Without a standardized KPI and driver framework, discussions about performance drivers (price, mix, cost, overheads) are fragmented.  
This Use Case acts as the central profitability dashboard for the enterprise and links to detailed Use Cases (margin analysis, cost drivers).

---

## 3. Key Questions
- How do revenue, gross margin, EBITDA, and net margin develop over time and by business unit?
- Which P&L lines (COGS, OpEx, SG&A) drive improvements or deterioration in profitability?
- Are we expanding margin in line with revenue growth or leaking margin?

---

## 4. Key KPIs
| KPI              | Definition                                      | Unit | Format   |
|------------------|-------------------------------------------------|------|----------|
| Net Sales Amount | Revenue net of returns and discounts            | EUR  | € #,0.00 |
| Gross Margin %   | (Net Sales – COGS) / Net Sales                  | %    | 1 decimal|
| EBITDA Margin %  | EBITDA / Net Sales                              | %    | 1 decimal|
| Net Margin %*    | Net Income / Net Sales (optional, if modeled)   | %    | 1 decimal|

(*Net Margin % can be added as KPI and measure once the P&L structure is available.)

---

## 5. Required Attributes (Business-Level)
- Org (region, business unit)
- P&L line structure (Net Sales, COGS, OpEx, EBITDA, Net Income)
- Amounts per period (month/quarter/year)

---

## 6. Segmentation & Hierarchies
- Org: Region > BusinessUnit  
- P&L: Revenue > Gross Margin > EBITDA > Net Income  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- P&L structure follows group reporting standards and maps 1:1 to the finance system.
- Adjusted measures (e.g., adjusted EBITDA) are documented separately if used.

---

## 8. Data Freshness & Cadence
- Data refresh: monthly (aligned with financial close).
- Quarterly deep dives for board reporting.

---

## 9. Edge Cases & QA Rules
- P&L totals must reconcile with official financial statements.
- Negative EBITDA or net margin periods are highlighted.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - P&L fact with amounts by Org, Period, PnLLine.
- Optional:
  - Scenario (Actual/Plan/Forecast), currency, consolidation adjustments.

---

## 11. Typical Actions
| Action                               | Code | Expected Effect          |
|--------------------------------------|------|--------------------------|
| Focus on loss-making business units  | SP1  | Improved overall margin  |
| Prioritize margin accretive growth   | SP2  | Higher profitability     |
| Align cost reduction with strategy   | O2   | Sustainable cost base    |

---

## 12. Expected Business Impact
| Dimension   | Expected Impact        | Measurement   |
|-------------|------------------------|---------------|
| Profitability| +0.5–1.0 pp EBITDA % | vs prior year |
| Transparency| Single version of truth| qualitative   |

---

## 13. Related Processes
Financial Close → Management Reporting → Performance Dialogue → Budget & Forecast.

---

## 14. Insights & Learnings
Typical findings include business units with strong growth but weak profitability, or cost categories that erode margin despite stable revenue.

---

## 15. Cross-References
- Related Use Cases:  
  `[COM-002 Gross Margin % vs Plan & Last Year](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  

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

