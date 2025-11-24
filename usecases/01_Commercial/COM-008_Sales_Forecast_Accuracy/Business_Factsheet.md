# Sales Forecast Accuracy - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and improve the accuracy and bias of sales forecasts by channel, region, and product hierarchy, in order to reduce firefighting, optimize inventory and capacity planning, and increase trust in the planning process.
- **Target Audience:** Head of Sales Planning / Demand Planning
- **Business Priority:** High
- **Expected Impact:** +5-10 pp forecast accuracy; lower safety stocks and firefighting.

## 2. Core Questions
- How accurate are our sales forecasts across regions, channels, and product hierarchies?
- Where do we systematically over- or under-forecast (bias) and why?
- Which combinations of product/channel/region show the highest error and volatility?
- How does forecast accuracy link to inventory days, service level, and working capital?

## 3. KPI Set (Business View)
| KPI                       | Definition                                              | Unit | Format   |
|---------------------------|---------------------------------------------------------|------|----------|
| Forecast Accuracy (MAPE)  | Mean absolute percentage error vs actual net sales     | %    | 1 decimal |
| Forecast Bias %           | (Forecast - Actual) / Actual                           | %    | 1 decimal |
| Actual Net Sales Amount   | Sum of actual net sales                                | EUR  |  #,0.00 |
| Forecast Net Sales Amount | Sum of forecasted net sales                            | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Exclude low-volume items below a minimum threshold when calculating MAPE.
- Validate that forecast and actuals share identical hierarchies and calendars.

## 5. Action Codes (Business Perspective)
| Action                                    | Code | Expected Effect                      |
|-------------------------------------------|------|--------------------------------------|
| Focus forecasting effort on volatile SKUs | P2   | MAPE improves on critical segments   |
| Adjust planning process where bias is high| SP1  | Lower bias and more stable volumes   |
| Align planning horizons and granularity   | I1   | Less re-planning and firefighting    |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Actual Net Sales Amount, Forecast Net Sales Amount, Forecast Accuracy (MAPE %), Forecast Bias % with Plan/LY deltas.
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
- Forecasts are frozen snapshots taken before the period starts (no rolling overrides).
- Actuals are net of returns and cancellations.
- MAPE and Bias are calculated only for periods with sufficient volume to avoid distortion.

## 8. Success Criteria
| Dimension       | Expected Impact              | Measurement     |
|-----------------|------------------------------|-----------------|
| Efficiency      | -10-20 % re-planning cycles | vs baseline     |
| Working Capital | -5-10 % inventory days      | vs prior year   |
| Service Level   | +1-2 pp service level       | vs prior year   |
