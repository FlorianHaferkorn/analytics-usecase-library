# SCM-001 – Business Factsheet

## 1. Summary
- **Business Goal:** Optimize inventory levels while maintaining service, reducing working capital and obsolescence.
- **Target Audience:** COO, Supply Chain, Demand Planning, Finance.
- **Business Priority:** High.
- **Expected Impact:** -10–20 % inventory, higher turns, fewer stockouts and write-offs.

## 2. Core Questions
- Where are inventory levels and DIO out of target by product/channel/location?
- Which items risk obsolescence or expiry?
- How do forecast accuracy and OTIF impact stockouts/overstocks?
- Which levers (policy, MOQ, lead time, safety stock) fix the biggest gaps?

## 3. KPI Set (Business View)

| KPI Name              | Purpose                          | Business Definition                      | Interpretation                    | Decision Relevance |
|-----------------------|----------------------------------|------------------------------------------|-----------------------------------|--------------------|
| Days in Inventory (DIO)| Inventory efficiency            | Avg Inventory / COGS × 365               | Lower = faster rotation           | WC lever           |
| Inventory Turnover     | Rotation speed                  | COGS / Avg Inventory                     | Higher = better use of capital    | Benchmark focus    |
| Stockout Rate %        | Service risk                    | Stockouts / Total order lines            | High = service issue              | Service actions    |
| OTIF %                 | Delivery reliability            | On-Time In-Full lines / Total lines      | High = reliable supply            | Supplier/actions   |
| Obsolescence Risk %    | Write-off risk                  | Aging/slow movers as % of inventory      | High = markdown/disposal risk     | Clearance actions  |

## 4. Business Logic & Thresholds
- DIO > target by >10 % = policy review.
- Stockout Rate > 3 % = safety stock or supply issue.
- OTIF < 95 % = supplier/logistics escalation.
- Obsolescence Risk > 8 % of value = markdown/phase-out.

## 5. Action Codes (Business Perspective)

| Code | Name                          | Business Description                       | Typical Trigger             | Expected Effect           |
|------|-------------------------------|--------------------------------------------|-----------------------------|---------------------------|
| I1   | Inventory Rebalance           | Reallocate across locations                | Stockouts + overstocks      | Better service, lower WC  |
| I2   | Policy Tuning                 | Safety stock, MOQ, lead time adjustments   | High DIO or stockouts       | Lower DIO, higher service |
| PC4  | Supplier/Logistics Fix        | Improve OTIF, lead time adherence          | OTIF < 95 %                 | Fewer stockouts           |
| D1   | Demand Signal Response        | Align to demand shifts and phase-outs      | Obsolescence risk rising    | Lower write-offs          |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: DIO, Inventory Turnover, Stockout %, OTIF %, Obsolescence Risk %.

### 6.2 30-Second Layer (Story)
- Bar: DIO/Turnover by product/location.
- Line: DIO and Stockout trend.
- Pareto: Obsolescence by SKU/category.

### 6.3 300-Second Layer (Detail)
- Matrix: Location → Category → SKU with DIO, Stockout %, OTIF, aging buckets.
- Drill to purchase orders and demand forecast accuracy.
- Export SKU actions (reorder, markdown, discontinue).

## 7. Dependencies & Constraints
- Accurate on-hand, receipts, issues, and aging data.
- Mapped SKUs to locations and channels.
- Forecast and lead time data for safety stock calc.

## 8. Success Criteria
- Lower DIO with stable or better service.
- Reduced obsolescence write-offs.
- OTIF improving to target, fewer stockouts.
- Factsheet used in weekly S&OP/WC huddles.
