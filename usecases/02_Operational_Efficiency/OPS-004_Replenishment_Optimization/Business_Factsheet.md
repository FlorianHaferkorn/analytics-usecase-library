# Replenishment Optimization & Service Level Management - Business Factsheet

## 1. Summary
- **Business Goal:** Optimize replenishment parameters and order logic to balance service levels, minimize inventory costs, and reduce lost sales due to stock-outs or delayed replenishment.
- **Target Audience:** Head of Supply Chain Planning
- **Business Priority:** High
- **Expected Impact:** +2-3 pp Service Level; -5-10 % Inventory Value; -20 % forecast MAPE

## 2. Core Questions
- Are replenishment quantities aligned with real demand and forecast accuracy?
- Which items or stores frequently under- or over-order?
- How does supplier lead time variability affect service levels?
- Where can replenishment frequency or batch sizes be optimized?
- Which actions yield the best trade-off between cost and service?

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Replenishment Adherence % | Orders placed / Orders suggested by system | % | 1 decimal |
| Order Accuracy % | Delivered Qty / Ordered Qty | % | 1 decimal |
| Stock-Out Rate % | Demand not fulfilled / Total demand | % | 1 decimal |
| Inventory Days | Inventory / COGS x 365 | days | 0 decimals |
| OTIF % | On-time, in-full deliveries / Total orders | % | 1 decimal |

## 4. Business Logic & Thresholds
- Reorder Point >= 0; Safety Stock >= 0.
- Negative order quantities excluded.
- Service Level % capped at [0; 100].
- Lead Time deviations > 3 standard deviations flagged.
- Referential integrity >= 99.9 % across Date/Org/Product/Supplier.

## 5. Action Codes (Business Perspective)
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Adjust reorder points based on forecast error and demand variability | I1 | Stock-Outs reduce; Inventory -5-10 % |
| Synchronize supplier delivery cadence with actual consumption patterns | PC4 | Lead Time reduces; OTIF improves |
| Implement dynamic safety stock based on target service level | I2 | Service improves; working capital stable |
| Reduce order batch sizes to avoid overstock | O2 | Inventory Days -5; obsolescence reduces |
| Integrate replenishment optimization into S&OP | SP1 | Forecast accuracy improves; liquidity improves |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Replenishment Adherence %, Order Accuracy %, Stock-Out Rate %, Inventory Days, OTIF % with Plan/LY deltas.
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
- Replenishment logic based on EOQ or Min/Max policy per SKU.
- Demand forecast updated weekly (rolling horizon).
- Lead times from supplier master, adjusted by historical average.
- Service Level Target defined by category (A: 98 %, B: 95 %, C: 90 %).
- Currency = EUR; values aggregated by store and category.

## 8. Success Criteria
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Service Level | +2-3 pp OTIF | vs Plan |
| Working Capital | Inventory value -5-10 % | vs Prior Quarter |
| Forecast Quality | MAPE -20 % | 13-week horizon |
