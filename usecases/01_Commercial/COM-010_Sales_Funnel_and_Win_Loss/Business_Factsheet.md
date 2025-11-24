# Sales Funnel & Win-Loss Analysis - Business Factsheet

## 1. Summary
- **Business Goal:** Provide transparency on the sales funnel from lead to close, understand win-loss reasons, and increase conversion and win rates by focusing efforts on the right segments and stages.
- **Target Audience:** Head of Sales / CRM Lead
- **Business Priority:** High
- **Expected Impact:** Higher conversion and win rates along the funnel; better pipeline quality.

## 2. Core Questions
- How much pipeline do we have by stage, segment, and region?
- What is our win rate overall and by segment/industry?
- Where do opportunities get stuck or drop out of the funnel?
- What are the main reasons for lost deals (price, product, service, competition)?

## 3. KPI Set (Business View)
| KPI                     | Definition                                   | Unit | Format   |
|-------------------------|----------------------------------------------|------|----------|
| Open Pipeline Amount    | Sum of amounts for open opportunities        | EUR  |  #,0.00 |
| Won Opportunities Amount| Sum of amounts for closed-won opportunities  | EUR  |  #,0.00 |
| Win Rate %              | Won Opportunities / (Won + Lost)            | %    | 1 decimal |
| Stage Conversion Rate % | % of opportunities moving from stage to stage| %    | 1 decimal |

## 4. Business Logic & Thresholds
- Opportunities without stage or status are flagged.
- Won and lost counts should reconcile with changes in pipeline.

## 5. Action Codes (Business Perspective)
| Action                                       | Code | Expected Effect                 |
|----------------------------------------------|------|---------------------------------|
| Focus coaching on weak funnel stages         | C1   | Higher conversion at bottlenecks|
| Adjust pricing or offering in high-loss areas| D1   | Higher win rate                 |
| Prioritize segments with high win rates      | P2   | More efficient use of sales time|

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Open Pipeline Amount, Won Opportunities Amount, Win Rate %, Stage Conversion Rate % with Plan/LY deltas.
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
- The CRM opportunity process is consistently used and stages are up to date.
- Amounts represent expected revenue (not necessarily recurring revenue).

## 8. Success Criteria
| Dimension | Expected Impact        | Measurement   |
|-----------|------------------------|---------------|
| Revenue   | +2-4 % closed revenue | vs prior year |
| Efficiency| +5-10 % sales productivity| vs baseline |
