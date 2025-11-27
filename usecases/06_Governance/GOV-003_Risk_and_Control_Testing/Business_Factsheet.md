---
id: "GOV-003"
title: "Risk & Control Testing"
domain: "Governance"
owner: "Head of Internal Audit / Risk Manager"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Governance Score %", "Audit Finding Severity %"]
supports_strategic_kpi_ids: ["gov.audit.findings.count", "gov.audit.findings.open.count"]
action_codes: ["G5"]
expected_impact: "+5 pp Control Pass Rate, -15 % Findings Severity."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Risk.Category>Process>Control",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter"
]
filters_default: [
  "Time: Last 12M",
  "Risk Category: All"
]
qa_asserts: ["RI_OK", "Controls_Tested", "Findings_Tracked"]
required_kpi_ids: [
  "gov.audit.findings.count",
  "gov.audit.findings.open.count"
]
required_kpis:
  gov.audit.findings.count: "Audit Findings Count"
  gov.audit.findings.open.count: "Open Audit Findings Count"
data_requirements:
  facts:
    - name: fact_controls
      grain: control_test
      primary_key: [ControlTestID]
      required_columns:
        - { name: ControlID, type: string, role: attribute }
        - { name: TestDate, type: date, role: date_key }
        - { name: Result, type: string, role: attribute }
    - name: fact_findings
      grain: finding
      primary_key: [FindingID]
      required_columns:
        - { name: FindingID, type: string, role: attribute }
        - { name: ControlID, type: string, role: attribute }
        - { name: Severity, type: string, role: attribute }
        - { name: IsOpen, type: bool, role: indicator }
        - { name: OpenDate, type: date, role: date_key }
  dims:
    - name: dim_control
      grain: control
      primary_key: [ControlID]
      required_columns:
        - { name: RiskCategory, type: string }
        - { name: Process, type: string }
        - { name: ControlName, type: string }
model_mapping:
  "Control Test Result": "fact_controls[Result]"
  "Control": "dim_control[ControlID]"
  "Finding Severity": "fact_findings[Severity]"
---

# GOV-003 Risk and Control Testing - Business Factsheet

## 1. Summary
- **Business Goal:** Demonstrate control effectiveness by consolidating testing outcomes and translating audit findings into prioritized remediation.
- **Target Audience:** Head of Internal Audit, Risk Management, Process Owners, Control Owners.
- **Business Priority:** High.
- **Expected Impact:** +5 pp control pass rate and -15 % findings severity through focused remediation.

## 2. Core Questions
- Which risk categories, processes, or controls fail most often during the test cycle?
- How many audit findings remain open, what is their severity, and how long have they been pending?
- Are remediation plans on track to close high-risk findings before the next assurance cycle?

## 3. KPI Set (Business View)
| KPI Name | Purpose | Business Definition | Interpretation | Decision Relevance |
|----------|---------|---------------------|----------------|--------------------|
| Audit Findings Count | Measures total control gaps detected in the period. | Number of findings logged during risk and control testing. | Rising count signals ineffective controls. | Determines remediation workload and executive communication. |
| Open Audit Findings Count | Shows remaining risk exposure. | Findings with IsOpen = true at period end. | High or aging backlog implies audit qualification risk. | Prioritizes remediation resources and escalations. |
| Control Pass Rate % | Indicates effectiveness of tested controls. | Passed tests / total tests executed (business-level ratio). | Target >= 90 %; < 80 % requires root-cause analysis. | Guides which processes need redesign or automation. |

## 4. Business Logic & Thresholds
- Controls failing twice in a row automatically join the high-risk focus list.
- Findings older than 180 days escalate to the Audit Committee (action code G5).
- Severity High findings require remediation plan approval within 15 business days.
- Control Pass Rate % excludes deferred tests to avoid artificial inflation.

## 5. Action Codes (Business Perspective)
| Code | Name | Business Description | Typical Trigger | Expected Effect |
|------|------|-----------------------|-----------------|------------------|
| G5 | Remediation Governance Board | Cross-functional forum to unblock overdue actions, align owners, and approve control redesign. | Open findings backlog > 20 % above target or severity mix skewed to High. | 50 % reduction of overdue findings within two quarters; improved pass rate. |

## 6. 3-30-300 Page Layout
### 6.1 3-Second Layer (Insight)
- KPI cards for Control Pass Rate %, Audit Findings Count, Open Audit Findings Count, and Aging category.
- Alert badge for overdue high-severity findings.

### 6.2 30-Second Layer (Story)
- Process/Risk heatmap showing pass vs fail distribution.
- Trend of findings raised/closed per quarter.
- Driver view linking failures to root causes (people, process, system).

### 6.3 300-Second Layer (Detail)
- Drillable register of tests with status, tester, evidence link, and remediation owner.
- Playbook style checklist capturing agreed mitigations and deadlines.
- Export-ready schedule for upcoming testing cycles.

## 7. Dependencies & Constraints
- Single control inventory with consistent IDs across testing and findings modules.
- Timely recording of test results and severity decisions (<= 3 business days after execution).
- Alignment with Internal Audit methodology (rating scale, sampling approach).
- Requires linkage to Jira/ServiceNow for remediation follow-up.

## 8. Success Criteria
- Leading: 95 % of test results logged within SLA; weekly adoption by risk and control owners.
- Lagging: Control Pass Rate % >= 90 %; >50 % reduction in open high-severity findings by year end.