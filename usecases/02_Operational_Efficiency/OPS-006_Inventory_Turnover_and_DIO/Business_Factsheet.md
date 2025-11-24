# Inventory Turnover & Days in Inventory (DIO) - Business Factsheet

## 1. Summary
- **Business Goal:** Monitor and optimize inventory turnover and days in inventory across products and locations to reduce working capital and obsolescence without harming service levels.
- **Target Audience:** Head of Supply Chain / Inventory Management
- **Business Priority:** High
- **Expected Impact:** -10-15 % inventory value; improved cash conversion and service level.

## 2. Core Questions
- What are our inventory turnover and DIO by product, location, and segment?
- Where do we carry excessive slow-moving or obsolete inventory?
- How do changes in demand or lead times impact optimal inventory levels?

## 3. KPI Set (Business View)
| KPI               | Definition                                  | Unit | Format   |
|-------------------|---------------------------------------------|------|----------|
| Inventory Turnover| COGS / Average Inventory Value              | x    | 1 decimal|
| Inventory Days    | 365 / Inventory Turnover                    | days | 0 decimals|
| DIO               | Days in Inventory (aligned with CCC)        | days | 0 decimals|

## 4. Business Logic & Thresholds
- Inventory values must be positive and non-null.
- DIO is capped at a defined maximum for outlier handling.

## 5. Action Codes (Business Perspective)
| Action                                 | Code | Expected Effect               |
|----------------------------------------|------|-------------------------------|
| Reduce safety stock for slow movers    | I1   | Lower inventory value         |
| Focus demand-shaping on overstock SKUs | I2   | Improved DIO and fewer write-offs |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Turnover, Inventory Days, Days in Inventory (DIO) with Plan/LY deltas.
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
- DIO is calculated on a yearly basis (365 days) unless specified differently.
- Average Inventory Value is calculated as (opening + closing) / 2 or via daily snapshots.

## 8. Success Criteria
| Dimension        | Expected Impact       | Measurement |
|------------------|-----------------------|-------------|
| Working Capital  | -10-15 % inventory   | vs prior year |
| Obsolescence     | -10-20 % write-offs  | vs baseline |
