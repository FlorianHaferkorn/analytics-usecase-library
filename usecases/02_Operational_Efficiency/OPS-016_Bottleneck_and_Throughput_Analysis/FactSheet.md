---
id: "OPS-016"
title: "Bottleneck & Throughput Analysis (TOC)"
domain: "Operational Efficiency"
owner: "Head of Operations / Plant Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["OEE %", "Productivity %"]
supports_strategic_kpi_ids:
  ["ops.oee.pct", "ops.performance.pct"]
action_codes: ["M2", "L2", "SP1"]
expected_impact: "Identify and manage production bottlenecks to increase overall throughput without immediate CAPEX investments."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Site>Line",
    "Asset.Family>Asset",
    "Time.Year>Month>Week>Day",
  ]
filters_default: ["Time: Last 3M", "Org: All"]
qa_asserts: ["Asset_ID_Consistent", "Routing_Defined"]
required_kpi_ids:
  [
    "ops.oee.pct",
    "ops.performance.pct",
    "ops.produced_units.qty",
  ]
required_kpis:
  ops.oee.pct: "Overall Equipment Effectiveness (OEE) %"
  ops.performance.pct: "Performance %"
  ops.produced_units.qty: "Produced Units Qty"
data_requirements:
  facts:
    - name: fact_production
      grain: production_run
      primary_key: [RunID]
      required_columns:
        - { name: RunID, type: string, role: attribute }
        - { name: AssetID, type: string, role: attribute }
        - { name: "Produced Units Qty", type: decimal, role: quantity }
        - { name: "Good Units Qty", type: decimal, role: quantity }
        - { name: "Run Start", type: datetime, role: date_key }
        - { name: "Run End", type: datetime, role: helper }
    - name: fact_mes_oee
      grain: asset_day
      primary_key: [AssetID, Date]
      required_columns:
        - { name: AssetID, type: string, role: attribute }
        - { name: Date, type: date, role: date_key }
        - { name: "OEE %", type: decimal, role: attribute }
        - { name: "Performance %", type: decimal, role: attribute }
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
    - { from: fact_production.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
    - { from: fact_mes_oee.AssetID, to: dim_asset.AssetID, cardinality: many-to-one, direction: single }
model_mapping:
  "Produced Units Qty": "fact_production[Produced Units Qty]"
  "Good Units Qty": "fact_production[Good Units Qty]"
  "OEE %": "fact_mes_oee[OEE %]"
  "Performance %": "fact_mes_oee[Performance %]"
  "Asset": "dim_asset[AssetID]"
  "Org": "dim_org[OrgID]"
---

# Bottleneck & Throughput Analysis (TOC)

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
