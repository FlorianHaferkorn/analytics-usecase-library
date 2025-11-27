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
expected_impact: "+5â€“15 % lines picked per hour; lower cost per order line."
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

# Warehouse Productivity & Picking Efficiency - Business Factsheet

## 1. Summary
- **Business Goal:** Increase warehouse productivity and picking efficiency by monitoring labor utilization and output per shift and DC.
- **Target Audience:** Head of Logistics / Warehouse Operations
- **Business Priority:** High
- **Expected Impact:** +5-15 % lines picked per hour; lower cost per order line.

## 2. Core Questions
- How many lines do we pick per hour per DC, zone, and shift?
- How does productivity differ across shifts, days, and sites?
- What is the labor cost per picked line, and how does it trend?
- Where can process changes, layout adjustments, or automation bring the largest gains?

## 3. KPI Set (Business View)
| KPI                     | Definition                           | Unit | Format   |
|-------------------------|--------------------------------------|------|----------|
| Lines Picked per Hour   | Order lines picked / labor hours     | #/h  | 1 decimal|
| Picks per Hour          | Picks count / labor hours            | #/h  | 1 decimal|
| Warehouse Cost per Line | Labor cost / order lines picked      | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Shifts with zero labor hours or zero picked lines are flagged.
- Labor cost must be positive and reconciled with payroll/finance data.

## 5. Action Codes (Business Perspective)
| Action                                | Code | Expected Effect                 |
|---------------------------------------|------|---------------------------------|
| Redesign picking routes/layout        | O2   | Higher lines per hour           |
| Introduce standardized picking methods| M1   | More consistent productivity    |
| Align staffing with volume patterns   | L2   | Lower cost per line             |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Lines Picked per Hour, Picks per Hour, Warehouse Cost per Order Line with Plan/LY deltas.
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
- Productivity is focused on picking; other activities (receiving, put-away) may be analyzed separately.
- Labor hours are accurately captured per shift and DC.

## 8. Success Criteria
| Dimension   | Expected Impact          | Measurement |
|-------------|--------------------------|-------------|
| Efficiency  | +5-15 % productivity    | vs baseline |
| Cost        | -5-10 % cost per line   | vs baseline |