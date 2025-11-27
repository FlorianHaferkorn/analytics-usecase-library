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

# Cybersecurity Incident Monitoring - Business Factsheet

## 1. Summary
- **Business Goal:** Monitor cybersecurity incidents across systems and business units to reduce critical events, improve response times, and support risk and compliance reporting.

---
- **Target Audience:** CISO / Head of IT Security
- **Business Priority:** High
- **Expected Impact:** Fewer critical incidents; faster detection and response; better compliance posture.

## 2. Core Questions
- How many cybersecurity incidents occurred by severity, category, and business unit?
- How many critical incidents did we have, and how quickly were they resolved (MTTR)?
- Are trends improving or deteriorating over time?
- Which systems or units show recurring issues?
---

## 3. KPI Set (Business View)
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| n/a | n/a | n/a | n/a |

## 4. Business Logic & Thresholds
- n/a

## 5. Action Codes (Business Perspective)
TODO: add action table.

## 6. 3-30-300 Page Layout

### 6.1 3-Second Layer (Insight)
- KPI cards for Cybersecurity Incident Count, Critical Incidents Count, Mean Time to Resolve (MTTR) Hours with Plan/LY deltas.
- Threshold coloring for immediate outliers.
- Short callout summarizing key variance.

### 6.2 30-Second Layer (Story)
- Trend chart (12-24M) for main KPIs.
- Variance bridge vs Plan/LY by driver.
- Ranking visuals for top/bottom segments.

### 6.3 300-Second Layer (Detail)
- Matrix/table with Org/Product/Initiative drill-down.
- Drill-through to financial plan vs actual detail.
- Export-ready table including action status.

## 7. Dependencies & Constraints
- n/a

## 8. Success Criteria
- n/a