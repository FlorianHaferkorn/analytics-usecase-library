# GOV-001 Data Quality Monitoring - Business Factsheet

## 1. Summary
- **Business Goal:** Ensure trusted reporting by continuously monitoring cross-domain data quality results and escalating deteriorating rules early.
- **Target Audience:** Chief Data Officer, Data Governance Office, Domain and Data Owners, BI Leads.
- **Business Priority:** High.
- **Expected Impact:** +2 pp Data Quality %, -20 % issue backlog through continuous monitoring and follow-up.

## 2. Core Questions
- Which domains, subject areas, and tables show the lowest Data Quality % this week or month?
- Which DQ rules fail most frequently and how severe is the downstream business impact?
- Are remediation owners resolving issues fast enough to protect regulatory and reporting commitments?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Data Quality % | Primary signal for trustworthiness of governed data assets. | Share of records that pass all active DQ rules out of the total validated records per table/day. | >= 97 % healthy, 95-97 % watchlist, < 95 % needs escalation. | Drives prioritization of remediation sprints and communication to business report owners. |
| Valid Records Count | Indicates the absolute volume of records that meet quality expectations. | Number of records per table/day that pass the configured DQ rules. | Sudden drops indicate ingestion issues or overly strict rules. | Guides capacity planning and triage for remediation teams. |
| Total Records Count | Baseline volume required to contextualize Data Quality %. | Total number of evaluated records per table/day. | Abnormal spikes may signal upstream pipeline defects; low volume can hide issues. | Helps size the impact range (customers, orders, transactions) affected by poor data quality. |

## 4. Business Logic & Thresholds
- Trigger action code G1 if Data Quality % stays below 95 % for two consecutive monitoring cycles.
- Valid Records Count must never exceed Total Records Count; mismatches require immediate root-cause analysis.
- Tables without monitored checks for more than 14 days are flagged as governance backlog.
- Domains with >20 % of tables in watchlist status move to executive review cadence.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| G1 | Data Steward Escalation | Mobilize the accountable steward to restore rule adherence and communicate business impact. | Data Quality % < 95 % for 2 cycles or repeated rule failures on critical tables. | +2 pp Data Quality % within one month; transparent owner communication. |
| G2 | Remediation Sprint | Cross-functional fix sprint covering ingestion, transformations, and rule tuning. | Multiple tables in the same domain fall below threshold or issue backlog grows >20 %. | -20 % open DQ issues, stabilized KPIs within the quarter. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Data Quality %, Valid Records Count, Total Records Count, Open Issues, and Top Critical Tables vs prior period.
- Highlight domains breaching thresholds with alert badges and steward contact.

### 6.2 30-Second Layer (Story)
- Heatmap Domain > Subject Area > Table with Data Quality % coloring.
- Trend chart (12-24 weeks) for Data Quality % and issue backlog.
- Breakdown of failed rules by severity and business owner.

### 6.3 300-Second Layer (Detail)
- Drillable table listing rule-level results, timestamps, and remediation status.
- Root-cause matrix (People, Process, Technology) to document learnings.
- Export-ready issue log including links to Jira/ServiceNow tickets.

## 7. Dependencies & Constraints
- DQ rules must be versioned with clear owner and severity; lineage to fact tables documented in the Data Catalog.
- Monitoring cadence at least weekly; automated scheduler writes historical snapshots.
- Steward directory (owner, backup, contact) needs to stay current for escalation workflows.
- Requires near-real-time access to operational logs capturing data pipeline status.

## 8. Success Criteria
- Leading: 95 % of steward escalations acknowledged within 2 business days; weekly dashboard adoption by Data Governance Office.
- Lagging: Sustained Data Quality % >= 97 % across top 10 critical tables; 20 % reduction of high-severity DQ issues quarter over quarter.
