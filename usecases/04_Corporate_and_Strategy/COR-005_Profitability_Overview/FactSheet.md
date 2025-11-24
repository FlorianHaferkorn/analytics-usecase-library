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

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
