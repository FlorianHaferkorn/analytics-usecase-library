# Stockout & Service Level - Business Factsheet

## 1. Summary
- **Business Goal:** Improve customer service levels by reducing stockouts and order errors across locations, products, and channels, while keeping inventory within targeted ranges.
- **Target Audience:** Head of Supply Chain / Customer Service
- **Business Priority:** High
- **Expected Impact:**  97-99 % service level with fewer stockouts and optimized inventory.

## 2. Core Questions
- What is our current OTIF and stockout rate by region, store, product, and channel?
- Where do stockouts cluster (by SKU, location, time), and what are the root causes?
- How do service levels correlate with inventory levels and forecast quality?

## 3. KPI Set (Business View)
| KPI            | Definition                                           | Unit | Format    |
|----------------|------------------------------------------------------|------|-----------|
| OTIF %         | On-time, in-full deliveries / total order lines      | %    | 1 decimal |
| Stockout Rate %| Lines with stockout / total requested lines          | %    | 1 decimal |
| Order Accuracy %| Correctly delivered lines / total delivered lines   | %    | 1 decimal |

## 4. Business Logic & Thresholds
- Orders without requested or delivered dates are flagged.
- OTIF and stockout rates must be calculated only for lines with complete information.

## 5. Action Codes (Business Perspective)
| Action                                  | Code | Expected Effect             |
|-----------------------------------------|------|-----------------------------|
| Address recurrent stockout SKUs/locations | I1  | Lower stockout rate         |
| Improve order picking and confirmation  | O2   | Higher OTIF and accuracy    |
| Align safety stocks with service targets| I2   | Stable service with less overstock |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for On-Time In-Full (OTIF) %, Stockout Rate %, Order Accuracy % with Plan/LY deltas.
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
- OTIF is defined based on agreed delivery window and completeness thresholds.
- Stockout is captured at order line level (no available inventory at requested date).

## 8. Success Criteria
| Dimension    | Expected Impact         | Measurement   |
|--------------|-------------------------|---------------|
| Service Level| +1-3 pp OTIF           | vs baseline   |
| Efficiency   | -5-10 % emergency orders| vs baseline  |
