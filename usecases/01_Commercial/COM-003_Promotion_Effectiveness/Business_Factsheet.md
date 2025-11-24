# Promotion Effectiveness (ROI & Uplift) - Business Factsheet

## 1. Summary
- **Business Goal:** Quantify the financial return of promotions by measuring incremental revenue and margin uplift versus baseline performance, and enable optimized calendar planning, depth, and targeting.
- **Target Audience:** Head of Marketing Controlling
- **Business Priority:** High
- **Expected Impact:** +10-30 % ROI uplift; +0.5-1.0 pp GM %; +1-3 pp Delta% NS

## 2. Core Questions
- Which promotions generated the highest incremental sales and margin uplift?
- What is the ROI of promotion spend by product, channel, and region?
- How do different promo mechanics (discount %, bundle, display) perform?
- What share of promotion volume was truly incremental versus cannibalized?
- Which calendar periods or channels deliver the best return on promo spend?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Promo ROI % | (Incremental GM - Promo Cost) / Promo Cost | % | 1 decimal |
| Promo Uplift % | (Promo Sales - Baseline Sales) / Baseline Sales | % | 1 decimal |
| Incremental Sales Amount | Promo Sales - Baseline Sales | EUR | 0-2 decimals |
| Incremental GM Amount | Promo GM - Baseline GM | EUR | 0-2 decimals |
| GM % During Promo | (Promo NS - Promo COGS) / Promo NS | % | 1 decimal |

## 4. Business Logic & Thresholds
- Exclude promos shorter than 2 days or with <5 transactions.
- ROI capped between [-100%; +500%] to avoid outlier bias.
- Ensure consistent baseline definition across products.
- Validate incremental uplift against total market trends.
- Referential integrity >= 99.9 % across Date/Org/Product/PromoID.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Optimize promotion calendar by ROI ranking | D1 | Delta% GM +0.5-1.0 pp; ROI +10-20 % |
| Reduce depth of low-return discounts | P2 | GM % +0.5 pp; NS stable |
| Focus investment on high-return mechanics | D2 | ROI +15-30 % |
| Improve baseline forecasting and promo tagging accuracy | O2 | Forecast bias reduces; reporting stability improves |
| Link trade marketing bonuses to measured ROI | SP1 | Long-term ROI alignment improves |

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
- Promo ROI = (Incremental GM - Promo Cost) / Promo Cost.
- Baseline defined as rolling average of non-promo periods (e.g., -8 to -2 weeks).
- Exclude overlapping promotions or multichannel effects for initial calculation.
- Cost data (promo budget) from Marketing Spend Plan.
- Reporting currency = EUR; FX at transaction date.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| ROI Improvement | +10-30 % ROI uplift | vs prior quarter |
| Profitability | +0.5-1.0 pp GM % | vs LY |
| Forecast Stability | -10 % forecast bias | Rolling 3M horizon |
