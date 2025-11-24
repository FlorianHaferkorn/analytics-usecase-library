---
id: "OPS-005"
title: "Capacity Utilization"
domain: "Operational Efficiency"
owner: "Head of Operations / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids: ["ops.oee.pct", "ops.process.cost_per_unit.amount"]
action_codes: ["M2", "L2"]
expected_impact: "+2 pp Utilization, -3 % Unit Cost by reducing idle time and balancing load."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Plant>Line",
  "Product.Family>SKU",
  "Time.Year>Month>Day>Shift"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Line: All"
]
qa_asserts: ["RI_OK", "Utilization_Within_0_100", "Hours_Reconcile"]
required_kpi_ids: [
  "ops.oee.pct",
  "ops.availability.pct",
  "ops.performance.pct",
  "ops.quality.pct",
  "ops.machine_downtime.pct",
  "ops.downtime.hours",
  "ops.planned.hours",
  "ops.produced_units.qty"
]
required_kpis:
  ops.oee.pct: "OEE %"
  ops.availability.pct: "Availability %"
  ops.performance.pct: "Performance %"
  ops.quality.pct: "Quality %"
  ops.machine_downtime.pct: "Downtime % of Planned"
  ops.downtime.hours: "Downtime Hours"
  ops.planned.hours: "Planned Production Hours"
  ops.produced_units.qty: "Produced Units"
data_requirements:
  facts:
    - name: fact_production
      grain: line_shift
      primary_key: [PlantID, LineID, ShiftDate, Shift]
      required_columns:
        - { name: PlantID, type: string, role: org_key }
        - { name: LineID, type: string, role: line_key }
        - { name: ShiftDate, type: date, role: date_key }
        - { name: Shift, type: string, role: attribute }
        - { name: PlannedHours, type: decimal, role: amount }
        - { name: DowntimeHours, type: decimal, role: amount }
        - { name: OutputUnits, type: decimal, role: quantity }
        - { name: GoodUnits, type: decimal, role: quantity }
        - { name: IdealCycleTime, type: decimal, role: helper }
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
        - { name: Plant, type: string }
    - name: dim_line
      grain: line
      primary_key: [LineID]
      required_columns:
        - { name: LineName, type: string }
        - { name: LineType, type: string }
  relationships:
    - { from: fact_production.ShiftDate, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_production.PlantID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_production.LineID, to: dim_line.LineID, cardinality: many-to-one, direction: single }
model_mapping:
  "Downtime Hours": "fact_production[DowntimeHours]"
  "Planned Hours": "fact_production[PlannedHours]"
  "Output Units": "fact_production[OutputUnits]"
  "Good Units": "fact_production[GoodUnits]"
---

# Capacity Utilization

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
