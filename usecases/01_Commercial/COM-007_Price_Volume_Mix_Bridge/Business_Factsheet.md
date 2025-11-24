# Price-Volume-Mix Bridge (Portfolio & Strategic View) - Business Factsheet

## 1. Summary
- **Business Goal:** Provide a strategic bridge that explains revenue and gross margin variance across the product and regional portfolio by decomposing into price, volume, and mix effects, enabling better planning and price governance.
- **Target Audience:** Head of Sales / Head of Finance
- **Business Priority:** High
- **Expected Impact:** Transparent decomposition of revenue and margin variances at portfolio level; better planning quality and price discipline.

## 2. Core Questions
- How much of portfolio-level Delta Net Sales and Delta Gross Margin comes from price, volume, and mix?
- Which categories or regions generate favorable mix effects, and which ones dilute margin?
- Where do pricing decisions erode margin despite volume growth?
- How do structural mix shifts (channel, region) impact strategic KPIs?

## 3. KPI Set (Business View)
| KPI                   | Definition                                   | Unit | Format   |
|-----------------------|----------------------------------------------|------|----------|
| Delta Net Sales Amount    | Net Sales - Net Sales LY                     | EUR  |  #,0.00 |
| Delta Gross Margin Amount | Gross Margin - Gross Margin LY               | EUR  |  #,0.00 |
| Price Effect Amount   | (Actual Price - LY Price)  Actual Volume    | EUR  |  #,0.00 |
| Volume Effect Amount  | (Actual Volume - LY Volume)  LY Price       | EUR  |  #,0.00 |
| Mix Effect Amount     | Delta Total - (Price Effect + Volume Effect)     | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Negative volumes and outlier prices are flagged.
- PVM reconciliation: Price + Volume + Mix  Delta Total (tolerance < 0.5 %).

## 5. Action Codes (Business Perspective)
| Action                                      | Code | Expected Effect             |
|---------------------------------------------|------|-----------------------------|
| Adjust pricing corridors for weak segments  | P2   | GM % improves, stable NS    |
| Focus growth on favorable mix categories    | M3   | GM % and NS both increase   |
| Re-balance regional/channel mix             | SP1  | More resilient profitability |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Delta Net Sales Amount vs LY, Delta Gross Margin Amount vs LY, Price Effect Amount, Volume Effect Amount, Mix Effect Amount with Plan/LY deltas.
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
- PVM is calculated vs Last Year or Plan with a consistent base definition.
- FX effects are handled separately or neutralized (constant currency).
- Promotions and one-offs are flagged to avoid misinterpreting structural price/mix effects.

## 8. Success Criteria
| Dimension     | Expected Impact                  | Measurement |
|---------------|----------------------------------|-------------|
| Profitability | +0.5-1.5 pp Gross Margin %      | vs LY       |
| Transparency  | 100 % reconciled NS & GM variances | bridge vs P&L |
