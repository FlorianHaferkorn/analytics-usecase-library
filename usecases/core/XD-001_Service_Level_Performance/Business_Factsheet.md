# XD-001 – Business Factsheet

## 1. Summary
- **Business Goal:** Maintain high service levels while controlling cost-to-serve across channels and regions.
- **Target Audience:** Customer Service, Supply Chain, Sales Ops, Finance.
- **Business Priority:** High.
- **Expected Impact:** ≥97–99 % service, fewer stockouts/backorders, reduced service penalties.

## 2. Core Questions
- Which channels/regions/customers have service gaps?
- What are the main drivers of missed service (stockouts, OTIF, order accuracy)?
- How do service issues translate into lost sales, credits, or penalties?
- Which actions deliver fastest service recovery?

## 3. KPI Set (Business View)

| KPI Name            | Purpose                         | Business Definition                         | Interpretation                  | Decision Relevance |
|---------------------|---------------------------------|---------------------------------------------|---------------------------------|--------------------|
| Service Level %     | Delivery performance            | Delivered in requested time/qty / total     | Core service indicator          | Customer impact    |
| Stockout Rate %     | Availability risk               | Stockouts / order lines                     | High = service risk             | Inventory actions  |
| OTIF %              | Reliability                     | On-Time In-Full / total deliveries          | Root cause for service          | Supplier/logistics |
| Order Accuracy %    | Execution quality               | Correct orders / total orders               | Low = process/quality issue     | Process fix        |
| Penalties/Credits   | Financial impact                | Penalties/credits due to service failures   | € leakage                       | Escalation         |

## 4. Business Logic & Thresholds
- Service Level < 97 % or trend down = immediate mitigation.
- Stockout Rate > 3 % = safety stock or supply fix.
- OTIF < 95 % = supplier/logistics escalation.
- Order Accuracy < 99 % = picking/process review.

## 5. Action Codes (Business Perspective)

| Code | Name                           | Business Description                      | Typical Trigger              | Expected Effect      |
|------|--------------------------------|-------------------------------------------|------------------------------|----------------------|
| I1   | Inventory Rebalance            | Reallocate/buffer critical SKUs           | Stockouts in priority areas  | Higher service       |
| PC4  | Supplier/Logistics Fix         | Address OTIF and lead time issues         | Low OTIF                     | Fewer misses         |
| O2   | Process Improvement            | Improve order accuracy, picking, ASN      | Low order accuracy           | Higher accuracy      |
| D1   | Demand Signal Response         | Adjust to demand swings quickly           | Demand shifts causing gaps   | Stabilize service    |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: Service Level %, Stockout %, OTIF %, Order Accuracy %, Penalties.

### 6.2 30-Second Layer (Story)
- Bar: Service Level by region/channel/customer.
- Line: Service Level and OTIF trend.
- Pareto: Penalties/credits by cause.

### 6.3 300-Second Layer (Detail)
- Matrix: Region → Channel → Customer with service KPIs.
- Drill: order lines with stockout/accuracy flags.
- Export action list with owners.

## 7. Dependencies & Constraints
- Order-level timestamps and requested vs delivered dates/qty.
- Stockout, OTIF, and accuracy flags aligned.
- Mapping to customer/channel/region.

## 8. Success Criteria
- Service ≥ target with stable trend.
- Reduced penalties/credits and fewer escalations.
- Lower stockouts/backorders with optimized buffers.
- Factsheet used in weekly service/ops reviews.
