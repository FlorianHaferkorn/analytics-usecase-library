# GOV-004 Audit Findings Management - Business Factsheet

## 1. Summary
- **Business Goal:** Close audit findings faster to reduce residual risk and demonstrate strong governance to regulators and the board.
- **Target Audience:** Internal Audit, Action Owners, Executive Sponsors.
- **Business Priority:** Medium (ongoing).
- **Expected Impact:** -15 % open findings and faster remediation through transparent ownership.

## 2. Core Questions
- How many audit findings are open, how old are they, and what severity do they carry?
- Which organizations or owners have the largest backlog or overdue items?
- Are remediation plans delivering the expected risk reduction and staying within agreed timelines?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Open Audit Findings Count | Shows outstanding remediation workload. | Number of findings with Status <> Closed. | Persistent backlog implies stalled remediation. | Used to size resources and escalate to executives. |
| Total Audit Findings Count | Provides context on overall assurance coverage. | All findings raised within the selected period. | Sudden spikes may relate to new audits or scope changes. | Helps prioritize cross-functional response capacity. |
| Findings Aging (Days) | Tracks timeliness of remediation. | Average days since OpenDate for open findings. | > 120 days indicates risk of audit qualification. | Informs whether to trigger action codes or reprioritize resources. |

## 4. Business Logic & Thresholds
- Findings aging > 120 days require executive escalation and inclusion in board reporting.
- Severity High findings must have approved action plan within 10 business days.
- Domains with >30 open findings trigger action code G5; repeated slippage on the same owner triggers G2.
- CloseDate cannot precede OpenDate; inconsistent records flagged for data correction.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| G2 | Remediation Sprint | Time-bound initiative to unblock overdue findings with dedicated SMEs. | Owner backlog exceeds plan or findings aging > 150 days. | -20 % backlog within one quarter; improved accountability. |
| G5 | Governance Review Board | Cross-functional steering to reprioritize resources and align deadlines. | Severity High backlog persists > 2 reporting cycles. | Balanced remediation plan, confirmed go-live dates, risk transparency. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Open Findings Count, Findings Aging, Severity mix, and On-track vs Overdue actions.
- Alert banner for overdue high-severity findings.

### 6.2 30-Second Layer (Story)
- Heatmap Org Region > Business Unit vs Severity.
- Timeline showing findings opened vs closed per month.
- Bar visual of owners ranked by overdue volume.

### 6.3 300-Second Layer (Detail)
- Drillable table with finding ID, description, owner, due date, blockers, and action code status.
- Checklist of remediation milestones and documents required for closure validation.
- Export table for regulatory evidence.

## 7. Dependencies & Constraints
- Integration with Internal Audit tooling to sync finding metadata, severity, and due dates.
- All owners and sponsors maintained in a master list for consistent routing.
- Requires timely status updates (weekly) from remediation owners.
- Data freshness <= 1 day to keep executive dashboards relevant.

## 8. Success Criteria
- Leading: 95 % of remediation status updates submitted on time; weekly dashboard usage by Internal Audit and key owners.
- Lagging: -15 % open findings quarter over quarter; >90 % of findings closed within agreed SLA.
