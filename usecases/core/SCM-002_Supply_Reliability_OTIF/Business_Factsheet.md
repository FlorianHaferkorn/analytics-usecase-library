# SCM-002 – Business Factsheet

## 1. Summary
- **Business Goal:** Improve supply reliability and OTIF performance to protect service and reduce penalties.
- **Target Audience:** Supply Chain, Logistics, Procurement, Customer Service.
- **Business Priority:** High.
- **Expected Impact:** OTIF ≥ 97 %, fewer chargebacks/penalties, lower emergency freight and buffer stock.

## 2. Core Questions
- Which suppliers, lanes, or DCs cause OTIF misses?
- What are the main root causes (planning, picking, transport, documentation)?
- How do OTIF issues translate into stockouts, lost sales, or penalties?
- Which corrective actions give fastest OTIF recovery?

## 3. KPI Set (Business View)

| KPI Name       | Purpose                           | Business Definition                       | Interpretation                    | Decision Relevance |
|----------------|-----------------------------------|-------------------------------------------|-----------------------------------|--------------------|
| OTIF %         | Supply reliability                | On-Time In-Full deliveries / total        | Core reliability KPI              | Supplier/logistics |
| On-Time %      | Punctuality                       | On-time deliveries / total                | Schedule adherence                | Transport actions  |
| In-Full %      | Completeness                      | Complete deliveries / total               | Fill rate reliability             | Inventory actions  |
| Stockout Rate %| Service risk                      | Stockouts / order lines                   | Impact to customer                | Service mitigation |
| Penalties/Cost | Financial impact                  | Chargebacks, expedites linked to OTIF     | € leakage                         | Escalation         |

## 4. Business Logic & Thresholds
- OTIF < 97 % or trend down = supplier/logistics escalation.
- On-Time < 95 % but In-Full high = transport/scheduling issue.
- In-Full < 97 % = picking/inventory problem.
- Penalties rising = immediate mitigation plan.

## 5. Action Codes (Business Perspective)

| Code | Name                         | Business Description                      | Typical Trigger                | Expected Effect      |
|------|------------------------------|-------------------------------------------|--------------------------------|----------------------|
| PC4  | Supplier/Logistics Fix       | Root-cause, SLA enforcement               | OTIF misses by supplier/lane   | Higher OTIF          |
| O2   | Process Improvement          | Picking/packing accuracy, ASN quality     | In-Full low                    | Fewer misses         |
| I1   | Inventory Rebalance          | Buffer critical SKUs where risk is high   | Stockout risk from OTIF issues | Service protection   |
| SP1  | Forecast/Plan Alignment      | Align forecasts with supply capacity      | Repeated misses due to plan gap| Fewer re-plans       |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: OTIF %, On-Time %, In-Full %, Stockout %, Penalties.

### 6.2 30-Second Layer (Story)
- Bar: OTIF by supplier/lane/DC with variance vs target.
- Pareto: Root causes of OTIF misses.
- Line: OTIF trend with On-Time and In-Full.

### 6.3 300-Second Layer (Detail)
- Matrix: Supplier → Lane/DC with OTIF, On-Time, In-Full, stockouts, penalties.
- Drill: shipment-level detail and ASN/booking accuracy.
- Export actions per supplier/lane.

## 7. Dependencies & Constraints
- Clean shipment data with timestamps, quantities, ASN status.
- Mapping to supplier, lane, DC, and customer orders.
- Link penalties/expedites to shipments.

## 8. Success Criteria
- OTIF ≥ target with stable trend.
- Reduced penalties/expedite cost.
- Lower stockouts linked to supply issues.
- Factsheet used in weekly supplier/logistics reviews.
