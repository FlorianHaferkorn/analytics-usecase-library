---
id: "OPS-009"
title: "Logistics Cost Ratio"
domain: "Operational Efficiency"
owner: "Head of Logistics / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Operating Cost Ratio %", "Working Capital %"]
supports_strategic_kpi_ids: ["fin.operating_cost_ratio.pct", "ops.working_capital.pct"]
action_codes: ["O2", "I1", "PC2"]
expected_impact: "-5â€“10 % logistics cost per unit; improved cost-to-serve."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>DC",
  "Channel",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Region: All",
  "DC: All"
]
qa_asserts: ["RI_OK", "Logistics_Cost_Reconciles", "Volume_Measures_Consistent"]
required_kpi_ids: [
  "ops.logistics.cost_ratio.pct",
  "ops.logistics.cost_per_unit.amount"
]
required_kpis:
  ops.logistics.cost_ratio.pct: "Logistics Cost Ratio %"
  ops.logistics.cost_per_unit.amount: "Logistics Cost per Unit"
data_requirements:
  facts:
    - name: fact_logistics_cost
      grain: dc_period
      primary_key: [CostID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Transport Cost Amount", type: decimal, role: amount }
        - { name: "Warehouse Cost Amount", type: decimal, role: amount }
        - { name: "Handling Cost Amount", type: decimal, role: amount }
    - name: fact_logistics_volume
      grain: dc_period
      primary_key: [VolumeID]
      required_columns:
        - { name: Date, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: "Shipped Units Qty", type: decimal, role: quantity }
        - { name: "Shipped Weight", type: decimal, role: helper }
        - { name: "Shipments Count", type: int, role: helper }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: Country, type: string }
        - { name: DC, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_logistics_cost.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_logistics_cost.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_logistics_volume.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_logistics_volume.Date, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Transport Cost Amount": "fact_logistics_cost[Transport Cost Amount]"
  "Warehouse Cost Amount": "fact_logistics_cost[Warehouse Cost Amount]"
  "Handling Cost Amount": "fact_logistics_cost[Handling Cost Amount]"
  "Shipped Units Qty": "fact_logistics_volume[Shipped Units Qty]"
  "Shipped Weight": "fact_logistics_volume[Shipped Weight]"
  "Shipments Count": "fact_logistics_volume[Shipments Count]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Logistics Cost Ratio - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and reduce logistics cost (transport, warehousing, handling) relative to shipped volume and revenue to improve cost-to-serve and profitability.
- **Target Audience:** Head of Logistics / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** -5-10 % logistics cost per unit; improved cost-to-serve.

## 2. Core Questions
- What is our logistics cost ratio (logistics cost / revenue) and cost per unit shipped?
- How do logistics costs differ across DCs, regions, and channels?
- Where can we optimize network design, carrier mix, or warehouse operations to reduce cost?

## 3. KPI Set (Business View)
| KPI                     | Definition                                      | Unit | Format   |
|-------------------------|-------------------------------------------------|------|----------|
| Logistics Cost Ratio %  | Total logistics cost / revenue or COGS         | %    | 1 decimal |
| Logistics Cost per Unit | Total logistics cost / shipped units           | EUR  |  #,0.000|
| Shipments per DC        | Number of shipments per DC/period              | #    | 0 decimals|

## 4. Business Logic & Thresholds
- DCs with zero shipped volume but costs are flagged.
- Cost and volume totals must reconcile with finance and operations views.

## 5. Action Codes (Business Perspective)
| Action                           | Code | Expected Effect              |
|----------------------------------|------|------------------------------|
| Consolidate shipments or routes | O2   | Lower cost per unit         |
| Optimize DC footprint            | I1   | Reduced total logistics cost|
| Renegotiate carrier contracts    | PC2  | Lower transport cost ratio  |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Logistics Cost Ratio %, Logistics Cost per Unit with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Customer drill-down.
- Drill-through to transactional detail (orders/invoices).
- Export-ready table including action status.

## 7. Dependencies & Constraints
- Allocation from corporate-level logistics cost to DCs is documented and stable.
- Revenue or COGS base for the ratio is defined consistently (not modeled in this Use Case, but assumed to exist).

## 8. Success Criteria
| Dimension   | Expected Impact        | Measurement |
|-------------|------------------------|-------------|
| Efficiency  | -5-10 % logistics cost| vs baseline |
| Profitability| +0.2-0.5 pp GM %     | vs baseline |