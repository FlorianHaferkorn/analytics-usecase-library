# Promotion ROI & Effectiveness - Business Factsheet

## 1. Summary
- **Business Goal:** Quantify the financial return of promotions by measuring incremental revenue and margin uplift versus baseline performance, and enable optimized promotion calendar, depth, and targeting across channels and regions.
- **Target Audience:** Head of Marketing Controlling / Trade Marketing
- **Business Priority:** High
- **Expected Impact:** +1-2 pp Gross Margin %, +3 % Net Sales in promoted lines

## 2. Core Questions
- Which promotions deliver the highest incremental sales and gross margin uplift?
- What is the ROI of promotion spend by product, channel, and region?
- How do different promotion mechanics (discount %, bundle, display) perform in terms of ROI versus volume impact?
- How much of promotion volume is truly incremental versus cannibalized from non-promoted products or periods?
- Where can we reduce ineffective promotions or re-invest into higher-ROI campaigns?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Promo ROI % | (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount | % | 1 decimal |
| Promo Uplift % | (Promo Sales Amount - Baseline Sales Amount) / Baseline Sales Amount | % | 1 decimal |
| Incremental Sales Amount | Promo Sales Amount - Baseline Sales Amount | EUR | 0-2 decimals |
| Incremental GM Amount | (Promo Sales - Promo COGS) - (Baseline Sales - Baseline COGS) | EUR | 0-2 decimals |
| GM % During Promo | (Promo Sales - Promo COGS) / Promo Sales | % | 1 decimal |

## 4. Business Logic & Thresholds
- Promotions with incomplete promo flags or missing cost data are flagged and excluded from ROI ranking.
- Baseline methods must be documented and consistent across products/channels.
- Uplift and ROI are only calculated when baseline and promo periods have sufficient data points.
- Referential integrity between sales and marketing spend tables should be >= 99.5 % on PromoID.
- Double counting across overlapping campaigns must be avoided or explicitly documented.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Stop or redesign low-ROI promotions | D1 | Promo ROI improves; GM % stabilizes |
| Increase depth or visibility of top-ROI promotions | D2 | Incremental GM and revenue increase |
| Optimize promotion calendar to avoid overlap | P2 | Cannibalization decreases; uplift quality improves |
| Align promo mechanics with price and margin strategy | M3 | Discount leakage reduces; GM % improves |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Promo ROI %, Promo Uplift %, Incremental Sales Amount, Incremental GM Amount, GM % During Promo with Plan/LY deltas.
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
- Promo ROI is defined as (Incremental GM Amount - Promo Cost Amount) / Promo Cost Amount.
- Baseline is derived from non-promo periods (e.g., average of last 8-12 weeks) and excludes overlapping campaigns.
- Cannibalization between products or channels is not explicitly modeled in the initial version; future versions may refine uplift attribution.
- Promo Cost Amount can be actuals or allocated from campaign budgets; allocation keys must be documented.
- Reporting currency is EUR; FX conversion at transaction date or monthly average.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Profitability | +1-2 pp Gross Margin % in promoted lines | vs Prior Year |
| Revenue | +3 % Net Sales in promoted categories | vs Prior Year |
| Efficiency | -10-20 % ineffective promo spend | vs baseline campaign plan |
