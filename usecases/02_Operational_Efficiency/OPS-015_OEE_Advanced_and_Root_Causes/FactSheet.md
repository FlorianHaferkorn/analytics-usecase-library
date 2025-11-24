---
id: "OPS-015"
title: "OEE Advanced & Root Causes"
domain: "Operational Efficiency"
owner: "Head of Manufacturing / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct"]
action_codes: ["M2", "L2", "O2"]
expected_impact: "Deep-dive OEE into availability, performance and quality losses by root cause to prioritize the most impactful improvement actions."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 3M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Downtime_Codes_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.availability.pct",
    "ops.performance.pct",
    "ops.quality.pct",
    "ops.downtime.hours",
    "ops.machine_downtime.pct",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.availability.pct: "Availability %"
  ops.performance.pct: "Performance %"
  ops.quality.pct: "Quality %"
  ops.downtime.hours: "Downtime Hours"
  ops.machine_downtime.pct: "Machine Downtime %"
data_requirements:
  facts:
    - name: fact_mes_oee
      grain: asset_day
      primary_key: [AssetID, Date]
      required_columns:
        - { name: AssetID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: "Availability %", type: decimal, role: attribute }
        - { name: "Performance %", type: decimal, role: attribute }
        - { name: "Quality %", type: decimal, role: attribute }
        - { name: "OEE %", type: decimal, role: attribute }
    - name: fact_mes_events
      grain: event
      primary_key: [EventID]
      required_columns:
        - { name: EventID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: StartTime, type: datetime, role: date_key }
        - { name: EndTime, type: datetime, role: helper }
        - { name: "Event Type", type: string, role: attribute }
        - { name: "Loss Category", type: string, role: attribute } # e.g. Availability, Performance, Quality
        - { name: "Loss Reason", type: string, role: attribute }
        - { name: "Downtime Hours", type: decimal, role: amount }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Site, type: string }
    - name: dim_asset
      grain: asset
      primary_key: [AssetID]
      required_columns:
        - { name: "Asset Family", type: string }
        - { name: "Line", type: string }
  relationships:
    - { from: fact_mes_oee.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_mes_events.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "OEE %": "fact_mes_oee[OEE %]"
  "Availability %": "fact_mes_oee[Availability %]"
  "Performance %": "fact_mes_oee[Performance %]"
  "Quality %": "fact_mes_oee[Quality %]"
  "Downtime Hours": "fact_mes_events[Downtime Hours]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# OEE Advanced & Root Causes

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
