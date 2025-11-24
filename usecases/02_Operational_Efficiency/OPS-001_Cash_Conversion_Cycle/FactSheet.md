---
id: "OPS-001"
title: "Cash Conversion Cycle (DSO + DIO - DPO)"
domain: "Operational Efficiency"
owner: "Head of Finance / Treasury"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Working Capital %", "Cash Conversion Cycle", "Operating Cash Flow"]
supports_strategic_kpi_ids: ["ops.working_capital.pct", "ops.working_capital.ccc.days", "fin.cashflow.ocf.amount"]
action_codes: ["W1", "I1", "W2", "O2", "SP1"]
expected_impact: "DSO -5-10 days; DIO -3-7 days; DPO +5-10 days; CCC -5-8 days"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Area>Store",
  "Product.Category>Subcategory>SKU",
  "Channel",
  "Time.Year>Month>Week"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Channel: All"
]
qa_asserts: ["RI_OK", "DSO_InRange", "CCC_Calculates"]
required_kpi_ids: [
  "ops.working_capital.dso.days",
  "ops.working_capital.dio.days",
  "ops.working_capital.dpo.days",
  "ops.working_capital.ccc.days",
  "ops.working_capital.ccc.delta_days"
]
required_kpis:
  ops.working_capital.dso.days: "DSO (Days)"
  ops.working_capital.dio.days: "DIO (Days)"
  ops.working_capital.dpo.days: "DPO (Days)"
  ops.working_capital.ccc.days: "CCC (Days)"
  ops.working_capital.ccc.delta_days: "Δ CCC (Days)"
data_requirements:
  facts:
    - name: fact_working_capital
      grain: period_end
      primary_key: [PeriodEndDate, OrgID]
      required_columns:
        - { name: "AR Balance", type: decimal, role: receivables }
        - { name: "AP Balance", type: decimal, role: payables }
        - { name: "Inventory Value", type: decimal, role: inventory }
        - { name: "Net Sales Amount", type: decimal, role: amount }
        - { name: "COGS Amount", type: decimal, role: amount }
        - { name: "Days In Period", type: int, role: helper }
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Entity, type: string }
  relationships:
    - { from: fact_working_capital.Date, to: dim_date.Date, cardinality: many-to-one, direction: single, ri_expected: ">=99.9%" }
    - { from: fact_working_capital.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
model_mapping:
  "AR Balance": "fact_working_capital[AR Balance]"
  "AP Balance": "fact_working_capital[AP Balance]"
  "Inventory Value": "fact_working_capital[Inventory Value]"
  "Net Sales Amount": "fact_working_capital[Net Sales Amount]"
  "COGS Amount": "fact_working_capital[COGS Amount]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
---
# Cash Conversion Cycle (DSO + DIO - DPO)

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md) - Ziele, KPIs, Action Codes und 3-30-300 Layout.
- [Technical_Factsheet.md](./Technical_Factsheet.md) - Data Contract, Semantic Model, DAX, RLS und QA.

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
