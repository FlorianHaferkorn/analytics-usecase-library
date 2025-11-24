# Inventory Health & Stock-Out Prevention - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure optimal stock levels by minimizing both overstock (capital tied up) and stock-outs (lost sales), balancing service levels and working capital efficiency.
- **Target Audience:** Head of Supply Chain / Logistics
- **Business Priority:** High
- **Expected Impact:** -10-15 % Inventory Value; >= 97 % OTIF; -20 % obsolescence

## 2. Core Questions
- Which SKUs or locations show excess or obsolete inventory?
- Where do stock-outs or low coverage threaten sales?
- What is the optimal target coverage given demand variability?
- How does forecast accuracy affect safety stock?
- What actions improve inventory turns without service loss?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Inventory Days | Inventory Value / COGS * 365 | days | 0 decimals |
| Stock-Out Rate % | Lost demand / Requested demand | % | 1 decimal |
| Inventory Turnover | COGS / Average Inventory | x | 1 decimal |
| Obsolescence % | (Aged Stock > Threshold) / Total Inventory | % | 1 decimal |
| OTIF % | On-Time In-Full Deliveries / Orders | % | 1 decimal |

## 4. Business Logic & Thresholds
- Inventory Value >= 0; Units Qty >= 0.
- Stock-Out Rate % <= 100 %.
- Referential integrity >= 99.9 % across Date/Org/Product.
- Exclude discontinued items from active coverage ratio.
- Safety Stock recalculated monthly based on updated demand volatility.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust replenishment parameters (min/max levels, reorder points) | I1 | DIO -5-10 days; Stock-Outs reduce |
| Prioritize allocation of limited stock to high-margin SKUs or key stores | I2 | Revenue loss reduces; service stability improves |
| Reduce obsolete inventory via targeted markdown or redistribution | O2 | Inventory value reduces 5-10 % |
| Improve forecast accuracy through demand segmentation | D1 | Service improves; DIO stable |
| Strengthen supplier reliability (lead time, fill rate) | PC4 | OTIF improves; Stock-Outs reduce |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Inventory Days, Stock-Out Rate %, Inventory Turnover, Obsolescence %, OTIF % with Plan/LY deltas.
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
- Inventory valued at standard cost; adjustments logged separately.
- Daily snapshots aggregated to month-end for trend analysis.
- Service Level = Delivered / Requested Qty; OTIF pulled from fulfillment system.
- Exclude consignment or third-party-managed stock.
- Currency = EUR; reporting by company code.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Working Capital | Inventory value -10-15 % | vs Plan |
| Service Level | OTIF >= 97 %; Stock-Out Rate <= 3 % | weekly dashboard |
| Obsolescence | Slow-mover share -20 % | vs Prior Quarter |
