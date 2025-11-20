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

## 1. Business Goal
Increase warehouse productivity and picking efficiency by monitoring labor utilization and output per shift and DC.

---

## 2. Business Context
Warehouse operations are labor-intensive and a major cost driver in logistics.  
Without a clear view on productivity (lines per hour, picks per hour) and cost per order line, it is difficult to identify improvement levers and benchmark sites.  
This Use Case standardizes key warehouse KPIs.

---

## 3. Key Questions
- How many lines do we pick per hour per DC, zone, and shift?
- How does productivity differ across shifts, days, and sites?
- What is the labor cost per picked line, and how does it trend?
- Where can process changes, layout adjustments, or automation bring the largest gains?

---

## 4. Key KPIs
| KPI                     | Definition                           | Unit | Format   |
|-------------------------|--------------------------------------|------|----------|
| Lines Picked per Hour   | Order lines picked / labor hours     | #/h  | 1 decimal|
| Picks per Hour          | Picks count / labor hours            | #/h  | 1 decimal|
| Warehouse Cost per Line | Labor cost / order lines picked      | EUR  | € #,0.00 |

---

## 5. Required Attributes (Business-Level)
- DC, zone, shift
- Labor hours and cost
- Order lines and picks per shift

---

## 6. Segmentation & Hierarchies
- Org: Region > DC > Zone  
- Time: Year > Month > Day > Shift  

---

## 7. Scope & Assumptions
- Productivity is focused on picking; other activities (receiving, put-away) may be analyzed separately.
- Labor hours are accurately captured per shift and DC.

---

## 8. Data Freshness & Cadence
- Data refresh: daily.
- Reporting cadence: daily/weekly operations review.

---

## 9. Edge Cases & QA Rules
- Shifts with zero labor hours or zero picked lines are flagged.
- Labor cost must be positive and reconciled with payroll/finance data.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Warehouse labor fact with hours and cost per shift/DC.
  - Warehouse activity fact with lines and picks per shift/DC.

---

## 11. Typical Actions
| Action                                | Code | Expected Effect                 |
|---------------------------------------|------|---------------------------------|
| Redesign picking routes/layout        | O2   | Higher lines per hour           |
| Introduce standardized picking methods| M1   | More consistent productivity    |
| Align staffing with volume patterns   | L2   | Lower cost per line             |

---

## 12. Expected Business Impact
| Dimension   | Expected Impact          | Measurement |
|-------------|--------------------------|-------------|
| Efficiency  | +5–15 % productivity    | vs baseline |
| Cost        | -5–10 % cost per line   | vs baseline |

---

## 13. Related Processes
Workforce Planning → Shift Scheduling → Picking Execution → Continuous Improvement.

---

## 14. Insights & Learnings
Typical findings include shifts or DCs with significantly lower productivity and mismatch between staffing and volume patterns.

---

## 15. Cross-References
- Related Use Cases:  
  `[OPS-005 Capacity Utilization](../OPS-005_Capacity_Utilization/FactSheet.md)`  
  `[OPS-009 Logistics Cost Ratio](../OPS-009_Logistics_Cost_Ratio/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

