# SCM-003 – Business Factsheet

## 1. Summary
- **Business Goal:** Improve forecast accuracy and bias to stabilize supply, inventory, and service.
- **Target Audience:** Supply Chain, Demand Planning, Finance, Sales Ops.
- **Business Priority:** High.
- **Expected Impact:** +5–10 pp forecast accuracy, fewer re-plans, lower safety stock and expedites.

## 2. Core Questions
- Where do forecasts deviate most vs actuals (by product, channel, region)?
- Is bias persistent (over- or under-forecasting)?
- How does forecast error drive stockouts, excess inventory, and service?
- Which items should move to more advanced forecasting or collaborative planning?

## 3. KPI Set (Business View)

| KPI Name             | Purpose                          | Business Definition                          | Interpretation                    | Decision Relevance |
|----------------------|----------------------------------|----------------------------------------------|-----------------------------------|--------------------|
| Forecast Accuracy %  | Overall forecast quality         | 1 - \|Actual - Forecast\| / Actual           | Higher = better                   | Planning confidence|
| MAPE %               | Error magnitude                  | Mean Absolute Percentage Error               | Lower = better                    | Model improvement  |
| Bias %               | Systematic over/under tendency   | (Forecast - Actual) / Actual                 | + = over, - = under               | Adjust process     |
| Service Impact %     | Orders impacted by forecast error| Stockout or expedite lines / total lines     | Impact to customers               | Mitigation         |
| Re-plan Frequency    | Process stability                | Number of plan changes per period            | High = unstable planning          | Process governance |

## 4. Business Logic & Thresholds
- Forecast Accuracy < 80 % for priority SKUs = model/process review.
- Bias > ±5 % for 2 periods = adjust planning inputs and collaboration.
- High re-plan frequency with stable demand = process discipline issue.
- Service Impact > 3 % of lines = safety stock or supply response.

## 5. Action Codes (Business Perspective)

| Code | Name                          | Business Description                       | Typical Trigger             | Expected Effect          |
|------|-------------------------------|--------------------------------------------|-----------------------------|--------------------------|
| SP1  | Forecast Discipline           | Governance, lock windows, consensus plan   | Bias or re-plans high       | Higher stability         |
| O2   | Process Improvement           | Improve data quality, segmentation         | Low accuracy for specific SKUs | Better forecasts    |
| I2   | Policy Tuning                 | Adjust safety stock for volatile items     | High error impacts service  | Higher service, stable WC|
| D1   | Demand Signal Integration     | Use POS/market signals for key SKUs        | Late demand signals         | Lower bias/error         |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: Forecast Accuracy %, MAPE %, Bias %, Service Impact %, Re-plan Frequency.

### 6.2 30-Second Layer (Story)
- Bar: Accuracy/Bias by product/channel/region.
- Line: Accuracy and Bias trend.
- Pareto: Service impact by SKU.

### 6.3 300-Second Layer (Detail)
- Matrix: Region → Channel → SKU with accuracy, bias, service impact.
- Drill: forecast version vs actuals; re-plan events.
- Export list of SKUs for model upgrade or collaboration.

## 7. Dependencies & Constraints
- Versioned forecasts with timestamps and horizons.
- Actuals aligned to same grain (SKU/channel/region).
- Clear planning calendar and lock periods.

## 8. Success Criteria
- Accuracy and bias improved and stable.
- Fewer re-plans; lower service impact from forecast error.
- Factsheet used in weekly S&OP and monthly IBP reviews.
