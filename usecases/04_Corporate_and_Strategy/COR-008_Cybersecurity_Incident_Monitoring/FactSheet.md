---
id: "COR-008"
title: "Cybersecurity Incident Monitoring"
domain: "Corporate and Strategy"
owner: "CISO / Head of IT Security"
impact: "High"
status: "Draft"
last_update: "19.11.2025"
maturity: "Idea"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Cyber Incident Count", "Regulatory Reporting Timeliness %"]
supports_strategic_kpi_ids: ["sec.incident.count", "gov.compliance.breach.count"]
action_codes: ["G3", "G4", "SP1"]
expected_impact: "Fewer critical incidents; faster detection and response; better compliance posture."
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "System>Application",
  "Incident.Severity>Category",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Severity: All",
  "System: All"
]
qa_asserts: ["RI_OK", "Incidents_Tracked", "Severity_Classification_Consistent"]
required_kpi_ids: [
  "sec.incident.count",
  "sec.incident.critical.count",
  "sec.incident.mttr.hours"
]
required_kpis:
  sec.incident.count: "Cybersecurity Incident Count"
  sec.incident.critical.count: "Critical Incidents Count"
  sec.incident.mttr.hours: "Mean Time to Resolve (MTTR) Hours"
data_requirements:
  facts:
    - name: fact_security_incidents
      grain: incident
      primary_key: [IncidentID]
      required_columns:
        - { name: IncidentID, type: string, role: attribute }
        - { name: "Detected Date", type: date, role: date_key }
        - { name: "Resolved Date", type: date, role: helper }
        - { name: "Severity", type: string, role: status }
        - { name: "Category", type: string, role: attribute }
        - { name: "Source System", type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
  dims:
    - name: dim_org
      grain: org
      primary_key: [OrgID]
      required_columns:
        - { name: Region, type: string }
        - { name: BusinessUnit, type: string }
    - name: dim_date
      grain: date
      primary_key: [Date]
      required_columns:
        - { name: Year, type: int }
        - { name: Month, type: int }
  relationships:
    - { from: fact_security_incidents.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_security_incidents."Detected Date", to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Incident ID": "fact_security_incidents[IncidentID]"
  "Severity": "fact_security_incidents[Severity]"
  "Category": "fact_security_incidents[Category]"
  "Detected Date": "fact_security_incidents[Detected Date]"
  "Resolved Date": "fact_security_incidents[Resolved Date]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Cybersecurity Incident Monitoring

## 1. Business Goal
Monitor cybersecurity incidents across systems and business units to reduce critical events, improve response times, and support risk and compliance reporting.

---

## 2. Business Context
Cybersecurity incidents (e.g., malware, phishing, access breaches) pose operational, financial, and reputational risks.  
Boards and regulators increasingly require transparent reporting on incidents, severities, and remediation status.  
This Use Case aggregates incident data and provides a structured view on volume, severity, and response times.

---

## 3. Key Questions
- How many cybersecurity incidents occurred by severity, category, and business unit?
- How many critical incidents did we have, and how quickly were they resolved (MTTR)?
- Are trends improving or deteriorating over time?
- Which systems or units show recurring issues?

---

## 4. Key KPIs
| KPI                     | Definition                                          | Unit | Format   |
|-------------------------|-----------------------------------------------------|------|----------|
| Cybersecurity Incident Count | Number of logged security incidents           | #    | 0 decimals|
| Critical Incidents Count| Number of incidents with highest severity          | #    | 0 decimals|
| MTTR Hours              | Average hours from detection to resolution         | h    | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Incident ID, detected/resolved dates
- Severity, category
- Source system/application
- Org (region, business unit)

---

## 6. Segmentation & Hierarchies
- Org: Region > BusinessUnit  
- System: System > Application  
- Time: Year > Quarter > Month  

---

## 7. Scope & Assumptions
- Incident logging is centralized and deduplicated across tools (SIEM, ticketing).
- Severity levels follow an agreed classification (e.g., Critical/High/Medium/Low).

---

## 8. Data Freshness & Cadence
- Incident data: near real-time or daily.
- Reporting cadence: monthly security review, quarterly risk committee.

---

## 9. Edge Cases & QA Rules
- Incidents without severity or dates are flagged.
- MTTR is calculated only for resolved incidents.

---

## 10. Minimum Viable Dataset (MVD)
- Required:
  - Incident fact with severity, timestamps, and org context.

---

## 11. Typical Actions
| Action                                      | Code | Expected Effect                    |
|---------------------------------------------|------|------------------------------------|
| Remediate recurring root causes             | G3   | Fewer critical incidents           |
| Strengthen controls in high-risk areas      | G4   | Lower incident volume              |
| Improve detection and response processes    | SP1  | Lower MTTR, reduced impact         |

---

## 12. Expected Business Impact
| Dimension | Expected Impact               | Measurement      |
|-----------|-------------------------------|------------------|
| Risk      | Fewer critical incidents      | vs baseline      |
| Compliance| Better audit/regulatory posture| qualitative      |

---

## 13. Related Processes
Threat Monitoring → Incident Detection → Response & Remediation → Reporting & Lessons Learned.

---

## 14. Insights & Learnings
Typical findings include specific applications or business units with disproportionate incident rates and processes that drive MTTR up or down.

---

## 15. Cross-References
- Related Use Cases:  
  `[GOV-002 Access & Compliance Review](../06_Governance/GOV-002_Access_and_Compliance_Review/FactSheet.md)`  
  `[GOV-003 Risk & Control Testing](../06_Governance/GOV-003_Risk_and_Control_Testing/FactSheet.md)`  

---

## 16. Review Information
| Field              | Value          |
|--------------------|----------------|
| Business Reviewer  | [Name / Role]  |
| Technical Reviewer | [Name / Role]  |
| Version            | v0.1           |
| Review Date        | DD.MM.YYYY     |
| Review Notes       | [Summary]      |

---

_Last updated: 19.11.2025_

