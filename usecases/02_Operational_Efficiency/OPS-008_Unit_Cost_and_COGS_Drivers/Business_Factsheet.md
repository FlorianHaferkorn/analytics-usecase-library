# Unit Cost & COGS Drivers - Business Factsheet

## 1. Summary
- **Business Goal:** Understand and reduce unit cost (cost per produced/sold unit) and COGS by decomposing them into main cost drivers such as material, labor, and energy.
- **Target Audience:** Head of Operations / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** -2-4 % unit cost; +0.5-1.0 pp gross margin %.

## 2. Core Questions
- What is our unit cost per product, line, and plant, and how has it evolved?
- How much of unit cost is driven by material, labor, energy, or other components?
- Where are the largest improvement opportunities (e.g., energy efficiency, labor productivity)?

## 3. KPI Set (Business View)
| KPI                  | Definition                                        | Unit | Format   |
|----------------------|---------------------------------------------------|------|----------|
| COGS Amount          | Total cost of goods sold                          | EUR  |  #,0.00 |
| Process Cost per Unit| (Sum of production costs) / produced units        | EUR  |  #,0.000|
| Material Cost Share %| Material cost / total production cost             | %    | 1 decimal|
| Labor Cost Share %   | Direct labor cost / total production cost         | %    | 1 decimal|

## 4. Business Logic & Thresholds
- Periods with zero or very low production volume are flagged to avoid distorted unit costs.
- Cost component sums must reconcile with total cost within a small tolerance.

## 5. Action Codes (Business Perspective)
| Action                               | Code | Expected Effect             |
|--------------------------------------|------|-----------------------------|
| Optimize material yields             | PC2  | Lower material cost share   |
| Improve line efficiency and uptime   | M1   | Lower unit cost             |
| Adjust product/plant allocations     | O2   | Better utilization and cost |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for COGS Amount, Process Cost per Unit with Plan/LY deltas.
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
- COGS is aligned with production cost attribution for the analysis period.
- Depreciation and overhead allocation rules are documented and, if included, applied consistently.

## 8. Success Criteria
| Dimension   | Expected Impact   | Measurement  |
|-------------|-------------------|--------------|
| Profitability| +0.5-1.0 pp GM % | vs baseline  |
| Efficiency  | -2-4 % unit cost  | vs baseline  |
