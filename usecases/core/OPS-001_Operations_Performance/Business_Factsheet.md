# OPS-001 – Business Factsheet

## 1. Summary
- **Business Goal:** Improve operational efficiency across plants/lines by monitoring OEE and throughput drivers.
- **Target Audience:** COO, Plant Managers, Operations Excellence, Maintenance.
- **Business Priority:** High.
- **Expected Impact:** +2–4 pp OEE, fewer bottlenecks, lower unit cost.

## 2. Core Questions
- Which lines/plants are underperforming on Availability, Performance, Quality?
- Where do downtime and speed losses happen most?
- How do throughput, scrap, and rework affect unit cost and service?
- Which actions unlock the highest OEE gains?

## 3. KPI Set (Business View)

| KPI Name          | Purpose                       | Business Definition                            | Interpretation                  | Decision Relevance |
|-------------------|-------------------------------|------------------------------------------------|---------------------------------|--------------------|
| OEE %             | Overall equipment efficiency  | Availability × Performance × Quality           | Core efficiency indicator       | Focus assets       |
| Availability %    | Uptime reliability            | Run Time / Planned Time                        | High downtime = maintenance gap | Maintenance plan   |
| Performance %     | Speed vs design               | Actual Speed / Design Speed                    | Speed losses                    | Process tuning     |
| Quality %         | Good Output share             | Good Units / Total Units                       | Scrap/rework impact             | Quality actions    |
| Throughput Units  | Volume delivered              | Good Units produced                            | Capacity output                 | Scheduling impact  |

## 4. Business Logic & Thresholds
- OEE < 75 % with negative trend = priority asset.
- Availability < 90 % = maintenance/root cause review.
- Performance < 90 % with stable availability = speed/recipe issue.
- Quality < 98 % = scrap/rework program.

## 5. Action Codes (Business Perspective)

| Code | Name                     | Business Description                     | Typical Trigger               | Expected Effect      |
|------|--------------------------|------------------------------------------|-------------------------------|----------------------|
| M2   | Maintenance Optimization | Planned vs unplanned downtime reduction  | Low Availability %            | +1–2 pp Availability |
| L2   | Productivity Boost       | Reduce speed losses, setup time          | Low Performance %             | +1–2 pp Performance  |
| O2   | Process Improvement      | Lean/Six Sigma to remove defects         | Low Quality %                 | +0.5–1.5 pp Quality  |
| PC4  | Capacity Balancing       | Load shift to less constrained assets    | Bottleneck throughput         | Higher throughput    |

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards: OEE %, Availability %, Performance %, Quality %, Throughput.

### 6.2 30-Second Layer (Story)
- Line: OEE and sub-KPIs trend.
- Bar: OEE by plant/line with variance vs target.
- Pareto: Downtime by reason category.

### 6.3 300-Second Layer (Detail)
- Matrix: Plant → Line → Shift with OEE breakdown.
- Drill: downtime reasons, scrap causes.
- Export action list with owner/ETA.

## 7. Dependencies & Constraints
- Reliable machine states (run/stop), shift calendar, and downtime coding.
- Good/bad quantity captured consistently.
- Clear target values per asset/class.

## 8. Success Criteria
- Sustained OEE improvement and reduced variability.
- Reduced unplanned downtime and scrap.
- Factsheet embedded in daily/weekly ops review.
