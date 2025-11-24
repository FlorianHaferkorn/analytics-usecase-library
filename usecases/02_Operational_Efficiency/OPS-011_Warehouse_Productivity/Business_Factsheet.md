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
