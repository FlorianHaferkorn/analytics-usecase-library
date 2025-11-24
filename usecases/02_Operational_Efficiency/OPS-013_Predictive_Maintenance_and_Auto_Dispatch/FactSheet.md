---
id: "OPS-013"
title: "Predictive Maintenance & Auto-Dispatch"
domain: "Operational Efficiency"
owner: "Head of Maintenance / Operations"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Operational"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["OEE %", "Productivity %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct", "fin.liquidity.working_capital"]
action_codes: ["M2", "L2", "O2"]
expected_impact: "Reduce unplanned downtime and maintenance cost by predicting failures and automatically scheduling technicians and spare parts."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 6M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Failure_Codes_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.availability.pct",
    "ops.downtime.hours",
    "ops.machine_downtime.pct",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.availability.pct: "Availability %"
  ops.downtime.hours: "Downtime Hours"
  ops.machine_downtime.pct: "Machine Downtime %"
data_requirements:
  facts:
    - name: fact_mes_events
      grain: event
      primary_key: [EventID]
      required_columns:
        - { name: EventID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: StartTime, type: datetime, role: date_key }
        - { name: EndTime, type: datetime, role: helper }
        - { name: "Event Type", type: string, role: attribute }
        - { name: "Failure Code", type: string, role: attribute }
    - name: fact_maintenance_orders
      grain: maintenance_order
      primary_key: [OrderID]
      required_columns:
        - { name: OrderID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Order Type", type: string, role: attribute }
        - { name: "TechnicianID", type: string, role: attribute }
        - { name: "Planned Start", type: datetime, role: date_key }
        - { name: "Actual Start", type: datetime, role: helper }
        - { name: "Actual End", type: datetime, role: helper }
        - { name: "Maintenance Cost Amount", type: decimal, role: amount }
    - name: fact_production
      grain: production_run
      primary_key: [RunID]
      required_columns:
        - { name: RunID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Planned Qty", type: decimal, role: quantity }
        - { name: "Produced Qty", type: decimal, role: quantity }
        - { name: "Good Qty", type: decimal, role: quantity }
        - { name: "Run Start", type: datetime, role: date_key }
        - { name: "Run End", type: datetime, role: helper }
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
        - { name: "Criticality", type: string }
  relationships:
    - { from: fact_mes_events.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_maintenance_orders.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_production.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "Downtime Hours": "fact_mes_events[Downtime Hours]"
  "Maintenance Cost Amount": "fact_maintenance_orders[Maintenance Cost Amount]"
  "Planned Qty": "fact_production[Planned Qty]"
  "Produced Qty": "fact_production[Produced Qty]"
  "Good Qty": "fact_production[Good Qty]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# Predictive Maintenance & Auto-Dispatch

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
