# OPS-002 – Business Factsheet

## 1. Summary
- **Business Goal:** Raise asset uptime and reliability while reducing maintenance cost and stockouts.
- **Target Audience:** COO, Maintenance, Reliability Engineering, Supply Chain.
- **Business Priority:** High.
- **Expected Impact:** Higher availability, fewer breakdowns, optimized spare parts, lower service disruption.

## 2. Core Questions
- Which assets show the highest downtime and failure frequency?
- What are the main root causes of unplanned downtime?
- How do maintenance plans and spare parts availability affect service/production?
- Which assets should we prioritize for overhaul or replacement?

## 3. KPI Set (Business View)

| KPI Name              | Purpose                         | Business Definition                         | Interpretation               | Decision Relevance      |
|-----------------------|---------------------------------|---------------------------------------------|------------------------------|-------------------------|
| Availability %        | Uptime performance              | Run Time / Planned Time                     | Lower = reliability issue    | Maintenance priority    |
| MTBF (hours)          | Reliability                     | Mean time between failures                  | Higher = more reliable       | Asset health            |
| MTTR (hours)          | Repair efficiency               | Mean time to repair                         | Lower = faster recovery      | Resourcing/spares       |
| Unplanned Downtime %  | Stability                       | Unplanned / Total downtime                  | High = process/maintenance gap | Preventive focus      |
| Spare Parts Stockout %| Readiness                       | Stockouts of critical parts                 | High = risk to uptime        | Inventory policy        |

## 4. Business Logic & Thresholds
- Availability < 95 % or trend down = reliability program.
- MTBF declining with rising MTTR = asset health degradation.
- Unplanned Downtime > 40 % of total = maintenance schedule redesign.
- Spare parts stockout > 5 % for critical parts = reorder policy change.

## 5. Action Codes (Business Perspective)

| Code | Name                          | Business Description                     | Typical Trigger                 | Expected Effect        |
|------|-------------------------------|------------------------------------------|---------------------------------|------------------------|
| M2   | Maintenance Optimization      | PM/CM mix, schedules, criticality-based  | High unplanned downtime         | +1–3 pp availability   |
| O2   | Root Cause Elimination        | Lean/Six Sigma on failure modes          | Recurring failures              | Higher MTBF            |
| PC4  | Spare Parts Policy Tuning     | Safety stock, reorder for critical parts | Stockout % above threshold      | Lower MTTR/stockouts   |
| L2   | Field Crew Productivity       | Improve dispatch/repair efficiency       | MTTR rising                     | Faster recovery        |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: Availability %, MTBF, MTTR, Unplanned Downtime %, Spare Parts Stockout %.

### 6.2 30-Second Layer (Story)
- Line: Availability, MTBF, MTTR trend.
- Pareto: Downtime by root cause.
- Bar: Availability by asset/plant.

### 6.3 300-Second Layer (Detail)
- Matrix: Asset → Component with downtime, MTBF, MTTR.
- Drill to work orders and part usage.
- Export action/maintenance plan.

## 7. Dependencies & Constraints
- CMMS/EAM work order data with cause codes.
- Asset hierarchy and criticality defined.
- Spare parts master with criticality and stock levels.

## 8. Success Criteria
- Availability and MTBF improving, MTTR declining.
- Lower share of unplanned downtime.
- Reduced stockout events on critical parts.
- Factsheet used in weekly maintenance and reliability meetings.
