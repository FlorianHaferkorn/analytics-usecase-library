# Replenishment & Safety Stock - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize replenishment parameters and safety stock levels to achieve target service levels at minimal inventory cost.
- **Target Audience:** Head of Supply Chain Planning
- **Business Priority:** High
- **Expected Impact:** +2-3 pp service level with -5-10 % inventory value.

## 2. Core Questions
- Are current safety stock levels appropriate given demand variability and lead times?
- Where do we see frequent backorders or stockouts despite high inventory?
- How do replenishment parameters (order quantities, lead times) impact service and inventory?

## 3. KPI Set (Business View)
| KPI               | Definition                                     | Unit | Format   |
|-------------------|------------------------------------------------|------|----------|
| Inventory Days    | Inventory / average daily demand               | days | 0 decimals|
| Stockout Rate %   | Backordered or unfulfilled demand / total demand | %  | 1 decimal |
| OTIF %            | On-time, in-full deliveries                    | %    | 1 decimal |
| Order Accuracy %  | Accurate orders / total orders                 | %    | 1 decimal |

## 4. Business Logic & Thresholds
- Negative on-hand quantities are flagged.
- Missing lead times are flagged; default assumptions documented.

## 5. Action Codes (Business Perspective)
| Action                                  | Code | Expected Effect                  |
|-----------------------------------------|------|----------------------------------|
| Adjust safety stock for volatile SKUs   | I1   | Lower stockouts, stable inventory|
| Rationalize replenishment parameters    | I2   | Fewer emergency orders           |
| Prioritize parameter review for high-value SKUs | SP1 | Higher service where it matters |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Days, Stockout Rate %, OTIF %, Order Accuracy % with Plan/LY deltas.
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
- Demand and inventory are measured at the same SKU/location/time grain.
- Safety stock policy is initially descriptive (no optimization engine embedded here).

## 8. Success Criteria
| Dimension     | Expected Impact          | Measurement   |
|---------------|--------------------------|---------------|
| Service Level | +2-3 pp OTIF            | vs baseline   |
| Working Capital| -5-10 % inventory value| vs baseline   |
