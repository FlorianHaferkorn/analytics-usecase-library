# Logistics Cost Ratio - Business Factsheet

## 1. Summary
- **Business Goal:** Measure and reduce logistics cost (transport, warehousing, handling) relative to shipped volume and revenue to improve cost-to-serve and profitability.
- **Target Audience:** Head of Logistics / Finance Controlling
- **Business Priority:** High
- **Expected Impact:** -5-10 % logistics cost per unit; improved cost-to-serve.

## 2. Core Questions
- What is our logistics cost ratio (logistics cost / revenue) and cost per unit shipped?
- How do logistics costs differ across DCs, regions, and channels?
- Where can we optimize network design, carrier mix, or warehouse operations to reduce cost?

## 3. KPI Set (Business View)
| KPI                     | Definition                                      | Unit | Format   |
|-------------------------|-------------------------------------------------|------|----------|
| Logistics Cost Ratio %  | Total logistics cost / revenue or COGS         | %    | 1 decimal |
| Logistics Cost per Unit | Total logistics cost / shipped units           | EUR  |  #,0.000|
| Shipments per DC        | Number of shipments per DC/period              | #    | 0 decimals|

## 4. Business Logic & Thresholds
- DCs with zero shipped volume but costs are flagged.
- Cost and volume totals must reconcile with finance and operations views.

## 5. Action Codes (Business Perspective)
| Action                           | Code | Expected Effect              |
|----------------------------------|------|------------------------------|
| Consolidate shipments or routes | O2   | Lower cost per unit         |
| Optimize DC footprint            | I1   | Reduced total logistics cost|
| Renegotiate carrier contracts    | PC2  | Lower transport cost ratio  |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Logistics Cost Ratio %, Logistics Cost per Unit with Plan/LY deltas.
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
- Allocation from corporate-level logistics cost to DCs is documented and stable.
- Revenue or COGS base for the ratio is defined consistently (not modeled in this Use Case, but assumed to exist).

## 8. Success Criteria
| Dimension   | Expected Impact        | Measurement |
|-------------|------------------------|-------------|
| Efficiency  | -5-10 % logistics cost| vs baseline |
| Profitability| +0.2-0.5 pp GM %     | vs baseline |
