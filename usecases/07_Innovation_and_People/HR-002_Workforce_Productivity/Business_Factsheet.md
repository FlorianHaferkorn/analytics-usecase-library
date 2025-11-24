# HR-002 Workforce Productivity - Business Factsheet

## 1. Summary
- **Business Goal:** Improve output per employee and reduce lost hours by combining financial KPIs with workforce availability insights.
- **Target Audience:** CHRO, People Analytics, Finance business partners, line managers.
- **Business Priority:** High due to cost pressure and tight labor markets.
- **Expected Impact:** +1 pp productivity per FTE and -0.5 pp absenteeism through targeted staffing, wellbeing, and automation initiatives.

## 2. Core Questions
- How do Revenue per FTE, Gross Margin per FTE, and Personnel Cost Ratio % trend across regions and departments?
- Which teams suffer from high absenteeism or capacity gaps that erode productivity?
- What actions (redeployment, automation, health programs) deliver the fastest productivity uplift?
- Are cost-to-serve and headcount plans aligned with actual workload and outcomes?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Revenue per FTE | Measures economic output per employee. | Net revenue allocated to an org divided by average FTE in the same period (business wording, no DAX). | Rising trend indicates efficiency gains; sharp drops flag underutilization. | Guides staffing levels and investment decisions. |
| Gross Margin per FTE | Focuses on value creation after COGS. | Gross margin allocated to an org divided by average FTE. | Keeps profitability view independent of revenue swings. | Aligns productivity targets with margin plans. |
| Personnel Cost Ratio % | Tracks cost of workforce relative to revenue. | Personnel costs / revenue for same org-period. | > Target (e.g., 32 %) implies cost pressure or revenue shortfalls. | Triggers cost-control or growth initiatives. |
| Absenteeism % | Shows lost capacity due to sickness or leave. | Absent hours / scheduled hours in period. | >4 % for white collar, >6 % for blue collar needs investigation. | Direct lever for wellbeing and staffing. |

## 4. Business Logic & Thresholds
- Productivity KPIs calculated on rolling 3-month windows to smooth seasonality.
- Personnel Cost Ratio % should stay within agreed corridor per business unit; breaches escalate to Finance lead.
- Absenteeism % thresholds vary by role type; dashboards highlight breaches per cohort.
- Manual overrides documented in governance log; unaligned Finance vs HR numbers blocked from publication.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| H3 | Workforce Rebalance Sprint | Reallocate FTE, adjust overtime, or backfill critical roles to restore productivity. | Revenue per FTE < target for 2 periods. | +1-2 pp productivity within a quarter. |
| H4 | Wellbeing and Attendance Program | Launch targeted health, ergonomics, or engagement actions to cut absenteeism. | Absenteeism % > threshold or repeated spikes. | -0.5 pp absenteeism; Personnel Cost Ratio stabilizes. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Revenue per FTE, Gross Margin per FTE, Personnel Cost Ratio %, Absenteeism % with plan/LY deltas.
- Alert banner for units breaching cost or absenteeism thresholds.

### 6.2 30-Second Layer (Story)
- Trend lines (12-24 months) for productivity KPIs and absenteeism.
- Variance bridge explaining Personnel Cost Ratio % vs plan (volume, mix, rate).
- Tree map Org Region > Business Unit ranking units by productivity.

### 6.3 300-Second Layer (Detail)
- Matrix Role > Level > Department with KPIs plus action code status.
- Table aligning staffing plan vs actual vs required FTE, including overtime impact.
- Drill-through to absenteeism driver log (reason codes, locations, seasonality).

## 7. Dependencies & Constraints
- Finance and HR must share the same org hierarchy codes and time buckets (monthly close).
- Headcount data includes employees, interns, contractors flagged separately; only employees count in KPI denominators.
- Scheduled vs absent hours captured with standardized reason codes; partial day absences normalized to hours.
- Personnel cost allocations follow Finance rules; restatements flagged in metadata notes.

## 8. Success Criteria
- Leading: 90 % of business units review productivity dashboard monthly; action codes logged within 5 days of breach.
- Lagging: +1 pp productivity per FTE and -0.5 pp absenteeism over 2 quarters; Personnel Cost Ratio % within target corridor.
