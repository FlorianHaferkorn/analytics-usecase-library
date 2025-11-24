# Channel Mix Performance - Business Factsheet

## 1. Summary
- **Business Goal:** Understand and optimize the performance of different sales channels (e.g., retail, e-commerce, wholesale) by measuring their contribution to revenue and margin, and steering channel mix towards strategic and profitable channels.
- **Target Audience:** Head of Sales / Head of Trade Marketing
- **Business Priority:** High
- **Expected Impact:** Shift channel mix towards higher-margin and strategic channels while protecting top-line growth.

## 2. Core Questions
- How is revenue and margin distributed across channels today, and how has the mix changed over time?
- Which channels deliver the highest contribution margin, and which ones dilute profitability?
- Are we overexposed to any single channel from a risk and dependency perspective?
- How do channel promotions and pricing strategies affect the mix?

## 3. KPI Set (Business View)
| KPI                        | Definition                                         | Unit | Format   |
|----------------------------|----------------------------------------------------|------|----------|
| Net Sales Amount           | Sum of net sales                                   | EUR  |  #,0.00 |
| Channel Revenue Share %    | Channel Net Sales / Total Net Sales                | %    | 1 decimal |
| Gross Margin %             | (Net Sales - COGS) / Net Sales                     | %    | 1 decimal |
| Channel Contribution Margin| Gross Margin allocated to channel                  | EUR  |  #,0.00 |

## 4. Business Logic & Thresholds
- Channel must be populated for all sales lines (> 99.5 % coverage).
- Channel share across all channels should sum to ~100 % per period.

## 5. Action Codes (Business Perspective)
| Action                                     | Code | Expected Effect                    |
|--------------------------------------------|------|------------------------------------|
| Shift promotions towards high-margin channels | M3 | Higher blended GM %                |
| Adjust trade terms in low-margin channels  | D1   | Margin dilution reduced            |
| Invest in digital channels with high GM %  | P2   | Growth in profitable channels      |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Net Sales Amount, Channel Revenue Share %, Gross Margin %, Channel Contribution Margin Amount with Plan/LY deltas.
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
- Allocation of shared costs to channels is out of scope initially; analysis is at gross margin level.
- Returns and discounts are included in Net Sales.

## 8. Success Criteria
| Dimension     | Expected Impact           | Measurement |
|---------------|---------------------------|-------------|
| Profitability | +0.5-1.0 pp Gross Margin %| vs prior year |
| Revenue       | +2-3 % Net Sales         | vs prior year |
