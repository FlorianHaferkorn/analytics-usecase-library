---
id: "OPS-017"
title: "OTIF Root Cause Analysis"
domain: "Operational Efficiency"
owner: "Head of Logistics / Supply Chain"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Service Level %", "Working Capital %"]
supports_strategic_kpi_ids:
  ["ops.otif.pct", "fin.liquidity.working_capital"]
action_codes: ["I1", "I2", "O2", "D1"]
expected_impact: "Explain OTIF deviations by root causes across planning, warehouse, transport and customer processes, and prioritize corrective actions."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments:
  [
    "Org.Region>DC",
    "Customer.Segment",
    "Time.Year>Month>Week",
  ]
filters_default: ["Time: Last 12M", "Org: All"]
qa_asserts: ["OTIF_Definition_Documented", "Event_Codes_Defined"]
required_kpi_ids:
  [
    "ops.otif.pct",
    "ops.order_accuracy.pct",
    "ops.stockout.pct",
  ]
required_kpis:
  ops.otif.pct: "On-Time-In-Full (OTIF) %"
  ops.order_accuracy.pct: "Order Accuracy %"
  ops.stockout.pct: "Stockout Rate %"
data_requirements:
  facts:
    - name: fact_deliveries
      grain: delivery
      primary_key: [DeliveryID]
      required_columns:
        - { name: DeliveryID, type: string, role: attribute }
        - { name: "Planned Delivery Date", type: date, role: date_key }
        - { name: "Actual Delivery Date", type: date, role: helper }
        - { name: OrgID, type: string, role: org_key }
        - { name: CustomerID, type: string, role: customer_key }
        - { name: "Delivered Lines Total", type: int, role: quantity }
        - { name: "Delivered Lines OTIF", type: int, role: quantity }
        - { name: "Delivered Lines Inaccurate", type: int, role: quantity }
        - { name: "Delivery Issue Code", type: string, role: attribute }
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
    - name: dim_customer
      grain: customer
      primary_key: [CustomerID]
      required_columns:
        - { name: Segment, type: string }
  relationships:
    - { from: fact_deliveries."Planned Delivery Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_deliveries.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_deliveries.CustomerID, to: dim_customer.CustomerID, cardinality: many-to-one, direction: single }
model_mapping:
  "Delivered Lines Total": "fact_deliveries[Delivered Lines Total]"
  "Delivered Lines OTIF": "fact_deliveries[Delivered Lines OTIF]"
  "Delivered Lines Inaccurate": "fact_deliveries[Delivered Lines Inaccurate]"
  "Date": "dim_date[Date]"
  "Org": "dim_org[OrgID]"
  "Customer": "dim_customer[CustomerID]"
---

# OTIF Root Cause Analysis

Dieses FactSheet wurde in separate Business- und Technical-Dokumente aufgeteilt.

- [Business_Factsheet.md](./Business_Factsheet.md)
- [Technical_Factsheet.md](./Technical_Factsheet.md)

Bitte nur noch die genannten Dateien pflegen; dieses Dokument bleibt fuer Legacy-Links bestehen.
