# COM-004 – Business Factsheet

## 1. Summary
- **Business Goal:** Measure the effectiveness and profitability of promotions by quantifying uplift, baseline vs promo performance and promo ROI.
- **Target Audience:** CCO, Category Management, Trade Marketing, Key Account Management, Controlling.
- **Business Priority:** High (promotion spend is one of the largest commercial cost blocks).
- **Expected Impact:** Fewer ineffective promotions, optimized budget allocation, improved promo profitability and better mechanism selection.

## 2. Core Questions
- Which promotions deliver real incremental value?
- How much sales/volume would we have generated without the promotion?
- What is the actual uplift vs the modeled baseline?
- How do promotions affect GM %, discount levels and price realization?
- Which mechanics (price cuts, multi-buy, flyer, display) perform best?
- Which retailers/channels over- or underperform in promotions?

## 3. KPI Set (Business View)

| KPI Name               | Purpose                                   | Definition                                                     | Interpretation                          | Decision Relevance           |
|------------------------|---------------------------------------------|----------------------------------------------------------------|------------------------------------------|------------------------------|
| Promo Uplift Qty       | Incremental volume                          | Promo Qty – Baseline Qty                                       | positive = added demand                  | enable mechanism decision    |
| Promo Uplift Amount    | Incremental revenue                         | Promo Sales – Baseline Sales                                   | business value of promotion              | budget allocation            |
| Baseline Sales Amount  | Expected sales without promotion            | Modeled baseline (historic/seasonal model)                     | separates natural trend vs promo effect   | control group logic          |
| Promo ROI              | Profitability of promotion                  | (Uplift Amount – Promo Cost) / Promo Cost                      | >0 = profitable                          | continue/stop decision       |
| Promo GM %             | Margin quality during promotion             | (Promo Sales – Promo COGS) / Promo Sales                       | low = over-discounting                   | pricing & mechanics review   |
| Promo Leakage Amount   | Margin loss driven by promotion            | (Baseline GM % – Promo GM %) × Promo Sales                     | quantifies economic loss                 | corrective actions           |

## 4. Business Logic & Thresholds
- Promo ROI < 0 = economically negative promotion.
- Promo Uplift Qty < +5 % = ineffective.
- Promo GM % significantly below normal GM % = risk of over-discounting.
- High Leakage Amount = priority for redesign or elimination.
- Repeated negative promotions = mandatory stop/redesign.

## 5. Action Codes

| Code | Name                   | Description                                 | Trigger                               | Expected Effect            |
|------|------------------------|---------------------------------------------|----------------------------------------|----------------------------|
| P2   | Discount Optimization  | Reduce/restructure discounts                | high discount %, low Promo GM %        | reduce leakage             |
| M1   | Mix Optimization       | Shift toward high-margin items              | weak mix                               | improve Promo GM %         |
| T1   | Promo Redesign         | Adjust mechanic (e.g., flyer → display)     | low uplift, low ROI                     | higher effectiveness       |
| T2   | Promo Termination      | Stop ineffective promotions                 | repeated negative ROI                   | protect budget             |
| C1   | Cost Review            | Validate cost-increase impact               | GM drop not driven by discount/mix      | stabilize GM %             |

## 6. 3–30–300 Page Layout

### **6.1 3-Second Layer**
- Promo Uplift Qty  
- Promo Uplift Amount  
- Promo ROI  
- Promo GM %  
- Promo Leakage Amount  

### **6.2 30-Second Layer**
- Ranking: uplifts, leakage, ROI
- Trend: ROI and GM % by month or by mechanic
- Decomposition: Promo Uplift vs Leakage vs Promo Cost

### **6.3 300-Second Layer**
- Detail Matrix by Promotion → Mechanic → Product
- Scatter: Discount % vs Promo ROI (outlier detection)
- Export view for Trade Marketing and KAM

## 7. Dependencies & Constraints
- Promotion indicator (PromoID or PromoFlag) required.
- Baseline model must be available (simple or advanced).
- Promo Cost needed for ROI.
- Price, discount and mix-related data from COM-001/002 improve interpretation.

## 8. Success Criteria
- Fewer negative-ROI promotions.
- Higher average Promo GM % and Promo ROI.
- Better promotional mechanics and retailer/channel selection.
- Regular use in category/trade/retailer reviews (>80 % adoption).
