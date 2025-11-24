# GOV-002 Access and Compliance Review - Business Factsheet

## 1. Summary
- **Business Goal:** Reduce unauthorized access and compliance violations by making entitlement reviews, issue remediation, and policy enforcement measurable.
- **Target Audience:** CISO, Compliance Officer, Internal Audit, Application Owners.
- **Business Priority:** High.
- **Expected Impact:** -10 % violations and breaches via structured access and compliance reviews.

## 2. Core Questions
- Which systems, applications, or roles generate the highest number of compliance incidents and breaches?
- How do incidents trend over time and across organizational units or severity bands?
- Where do overdue reviews, missing attestations, or open remediation items block compliance sign-off?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Compliance Incidents Count | Quantifies total detected violations for transparency and prioritization. | Number of recorded incidents within the selected period, grouped by system or org. | Upward trend indicates ineffective controls or backlog. | Determines where to run targeted reviews or training. |
| Compliance Breach Count | Focuses on breaches with regulatory impact that require immediate action. | Count of incidents marked as breach (IsBreach = true). | Any breach triggers formal escalation; 0 is target. | Guides reporting to regulators and executive steering. |
| Incident Closure Rate % | Shows how quickly incidents are resolved after discovery. | Closed incidents / total incidents in period (business-only ratio, no DAX detail). | < 90 % closure indicates process bottlenecks. | Helps size remediation squads and escalate to system owners. |

## 4. Business Logic & Thresholds
- Breach Count > 0 automatically triggers action code G3 plus regulatory notification workflow.
- Incident Closure Rate % < 90 % for two consecutive months surfaces in executive compliance report.
- Severity High incidents must be acknowledged within 24 hours; SLA breaches escalate to CISO.
- All critical applications require at least quarterly entitlement reviews; overdue items flagged.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| G3 | Access Cleanup Wave | Structured removal of obsolete roles and accounts plus targeted retraining. | Repeated incidents on the same system or >5 breaches in quarter. | -30 % incidents on affected system, restored policy compliance. |
| G4 | Control Reinforcement | Introduce or tighten detective/preventive controls (MFA, SoD, approvals). | SLA breaches, repeated violations in high-risk processes. | Breach Count returns to 0; audit comfort restored. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Compliance Incidents Count, Compliance Breach Count, Incident Closure Rate %, and Open Reviews.
- Callout describing most critical system/role breaching policy.

### 6.2 30-Second Layer (Story)
- Trend chart (12M) per KPI with severity overlays.
- Tree map System > Application > Role for incident concentration.
- Table linking incidents to accountable owners and SLA status.

### 6.3 300-Second Layer (Detail)
- Drill-down to incident detail with timestamps, classification, remediation owner.
- Checklist view of upcoming/overdue access reviews by org.
- Exportable audit evidence (CSV/PDF) for attestation.

## 7. Dependencies & Constraints
- Central incident register covering ERP, CRM, BI, and infrastructure systems; uniform severity taxonomy.
- Governance calendar for periodic access recertification per system including owner assignments.
- Integration with ticketing system to track remediation workflow stages.
- Data latency <= 24 hours to ensure near real-time oversight.

## 8. Success Criteria
- Leading: 95 % of access reviews completed before deadline; dashboard adoption by compliance and system owners every month.
- Lagging: -10 % incidents overall and 0 breaches for critical systems across the quarter; reduced external audit findings on access controls.
