---
id: "OPS-011"
title: "Warehouse Productivity & Picking Efficiency"
domain: "Operational Efficiency"
owner: "Head of Logistics / Warehouse Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids: ["ops.oee.pct", "ops.warehouse.productivity.pct"]
action_codes: ["O2", "M1", "L2"]
expected_impact: "+5–15 % lines picked per hour; lower cost per order line."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>DC>Zone",
  "Time.Year>Month>Day>Shift"
]
filters_default: [
  "Time: Last 3M",
  "DC: All"
]
qa_asserts: ["RI_OK", "Lines_Per_Hour_InRange", "Labor_Hours_Tracked"]
required_kpi_ids: [
  "ops.warehouse.lines_per_hour",
  "ops.warehouse.picks_per_hour",
  "ops.warehouse.cost_per_line.amount"
]
required_kpis:
  ops.warehouse.lines_per_hour: "Lines Picked per Hour"
  ops.warehouse.picks_per_hour: "Picks per Hour"
  ops.warehouse.cost_per_line.amount: "Warehouse Cost per Order Line"
data_requirements:
  facts:
    - name: fact_wh_labor
      grain: dc_shift
      primary_key: [LaborID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Shift", type: string, role: attribute }
        - { name: "Labor Hours", type: decimal, role: helper }
        - { name: "Labor Cost Amount", type: decimal, role: amount }
    - name: fact_wh_activity
      grain: dc_shift
      primary_key: [ActivityID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Shift", type: string, role: attribute }
        - { name: "Order Lines Picked", type: int, role: helper }
        - { name: "Picks Count", type: int, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: DC, type: string }
        - { name: Zone, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Day, type: int }
  relationships:
    - { from: fact_wh_labor.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_wh_labor.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_wh_activity.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_wh_activity.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Labor Hours": "fact_wh_labor[Labor Hours]"
  "Labor Cost Amount": "fact_wh_labor[Labor Cost Amount]"
  "Order Lines Picked": "fact_wh_activity[Order Lines Picked]"
  "Picks Count": "fact_wh_activity[Picks Count]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Warehouse Productivity & Picking Efficiency

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
