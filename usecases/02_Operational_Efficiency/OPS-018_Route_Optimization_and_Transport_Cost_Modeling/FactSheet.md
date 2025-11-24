---
id: "OPS-018"
title: "Route Optimization & Transport Cost Modeling"
domain: "Operational Efficiency"
owner: "Head of Logistics / Transport Planning"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Prescriptive"
supports_strategic_kpi: ["Operating Cost Ratio %", "Service Level %"]
supports_strategic_kpi_ids:
  ["ops.logistics.cost_ratio.pct", "ops.otif.pct"]
action_codes: ["O2", "I1", "PC2"]
expected_impact: "Reduce transport cost while maintaining service level by optimizing routes, loads and transport modes based on demand and constraints."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>DC",
    "Transport.Route>Stop",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 13W", "Org: All"]
qa_asserts: ["Transport_Cost_Allocation_Documented", "Route_Master_Consistent"]
required_kpi_ids:
  [
    "ops.logistics.cost_ratio.pct",
    "ops.logistics.cost_per_unit.amount",
    "ops.otif.pct",
  ]
required_kpis:
  ops.logistics.cost_ratio.pct: "Logistics Cost Ratio %"
  ops.logistics.cost_per_unit.amount: "Logistics Cost per Unit"
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
data_requirements:
  facts:
    - name: fact_transport
      grain: shipment
      primary_key: [ShipmentID]
      required_columns:
        - { name: ShipmentID, type: string, role: attribute }
        - { name: "Route ID", type: string, role: attribute }
        - { name: "Departure Date", type: date, role: date_key }
        - { name: "Transport Cost Amount", type: decimal, role: amount }
        - { name: "Shipped Units Qty", type: decimal, role: quantity }
        - { name: "Distance Km", type: decimal, role: attribute }
  dims:
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
        - { name: Week, type: int }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: "Distribution Center", type: string }
    - name: dim_route
      grain: route
      primary_key: ["Route ID"]
      required_columns:
        - { name: "Route Name", type: string }
        - { name: "Transport Mode", type: string }
  relationships:
    - { from: fact_transport."Departure Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    # OrgID may come from DC or shipping org, simplified here
model_mapping:
  "Transport Cost Amount": "fact_transport[Transport Cost Amount]"
  "Shipped Units Qty": "fact_transport[Shipped Units Qty]"
  "Distance Km": "fact_transport[Distance Km]"
  "Route ID": "fact_transport[Route ID]"
  "Route Name": "dim_route[Route Name]"
  "Date": "dim_date[Date]"
---

# Route Optimization & Transport Cost Modeling

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
