---
id: "COR-002"
title: "Workforce Productivity & Turnover Analysis"
domain: "Corporate and Strategy"
owner: "Head of HR Controlling / People Analytics"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Revenue per FTE", "Personnel Cost Ratio %", "Turnover Rate %"]
supports_strategic_kpi_ids: ["hr.revenue_per_fte.amount", "hr.personnel_cost_ratio.pct", "hr.turnover.pct"]
action_codes: ["C1", "SP1", "O2", "D1", "O3"]
expected_impact: "+5-10 % Revenue per FTE; -2-4 % Personnel Cost Ratio; +3-5 pp turnover improvement"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>Country>Department",
  "Workforce.Function>Team",
  "Employee.Seniority>Tenure",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Org: All",
  "Function: All"
]
qa_asserts: ["RI_OK", "Headcount_Positive", "Turnover_Range"]
required_kpi_ids: [
  "hr.revenue_per_fte.amount",
  "hr.gm_per_fte.amount",
  "hr.personnel_cost_ratio.pct",
  "hr.turnover.pct",
  "hr.absenteeism.pct"
]
required_kpis:
  hr.revenue_per_fte.amount: "Revenue per FTE"
  hr.gm_per_fte.amount: "Gross Margin per FTE"
  hr.personnel_cost_ratio.pct: "Personnel Cost Ratio %"
  hr.turnover.pct: "Turnover Rate %"
  hr.absenteeism.pct: "Absenteeism %"
data_requirements:
  facts:
    - name: fact_hr_headcount
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: EmployeeID, type: string, role: employee_key }
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: OrgID, type: string, role: org_key }
        - { name: Department, type: string, role: attribute }
        - { name: Function, type: string, role: attribute }
        - { name: Country, type: string, role: attribute }
        - { name: FTEFactor, type: decimal, role: helper }
        - { name: ContractType, type: string, role: attribute }
        - { name: HireDate, type: date, role: helper }
        - { name: LeaveDate, type: date, role: helper }
    - name: fact_hr_cost
      grain: employee_month
      primary_key: [EmployeeID, SnapshotMonth]
      required_columns:
        - { name: PersonnelCost, type: decimal, role: amount }
        - { name: BonusCost, type: decimal, role: amount }
        - { name: OvertimeCost, type: decimal, role: amount }
    - name: fact_financials
      grain: org_month
      primary_key: [OrgID, SnapshotMonth]
      required_columns:
        - { name: RevenueAmount, type: decimal, role: amount }
        - { name: GrossMarginAmount, type: decimal, role: amount }
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
  relationships:
    - { from: fact_hr_headcount.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_hr_headcount.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_hr_cost.EmployeeID, to: fact_hr_headcount.EmployeeID, cardinality: many-to-one, direction: single }
    - { from: fact_financials.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_financials.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
model_mapping:
  "Employee": "fact_hr_headcount[EmployeeID]"
  "Region": "dim_org[Region]"
  "Department": "fact_hr_headcount[Department]"
  "FTE": "fact_hr_headcount[FTEFactor]"
  "Personnel Cost": "fact_hr_cost[PersonnelCost]"
  "Revenue Amount": "fact_financials[RevenueAmount]"
  "Gross Margin Amount": "fact_financials[GrossMarginAmount]"
  "Snapshot Month": "fact_hr_headcount[SnapshotMonth]"
---

# Workforce Productivity & Turnover Analysis

## 1. Business Goal
Improve organizational efficiency and employee retention by tracking productivity, cost, and turnover trends - enabling data-driven workforce planning and early identification of risk areas.

---

## 2. Business Context
People costs are one of the largest expense items, yet HR and Finance often run disconnected analyses. HR cares about turnover and engagement, Finance about productivity and cost ratios. This use case establishes a single source of truth linking headcount, cost, and output so executives can steer staffing plans, identify hot spots, and justify investments in retention or automation. It also provides early warning signals when attrition threatens service or sales capacity.

---

## 3. Key Questions
- How has productivity evolved per department, region, or function?
- What are the main drivers of workforce cost increases?
- Which segments show high turnover or absenteeism risk?
- What is the cost impact of employee churn?
- How does engagement or tenure correlate with performance?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Revenue per FTE | Revenue / Average FTE | EUR | 0 decimals |
| Gross Margin per FTE | GM / Average FTE | EUR | 0 decimals |
| Personnel Cost Ratio % | Personnel Cost / Revenue | % | 1 decimal |
| Turnover Rate % | Exits / Average Headcount | % | 1 decimal |
| Absenteeism % | Absent hours / Scheduled hours | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Employee ID (anonymized or aggregated)
- Org Unit, Department, Country
- Hire Date, Leave Date, Status (Active/Exited)
- FTE Factor, Contract Type (Full/Part-Time)
- Net Sales Amount, Gross Margin Amount, Personnel Cost
- Optional: Age Group, Tenure, Engagement Score, Job Level

---

## 6. Segmentation & Hierarchies
- Org: Region > Country > Department > Team
- Function: Sales / Operations / Support / Corporate
- Workforce Type: Permanent / Temporary / Contractor
- Tenure: <1y, 1-3y, 3-5y, >5y
- Time: Year > Quarter > Month

---

## 7. Scope & Assumptions
- Productivity = output (Sales, Margin) / workforce input (FTEs, Cost).
- Turnover = exits / average headcount over period.
- Personnel Cost includes salaries, bonuses, social costs.
- FTE values standardized to 1.0 for full-time equivalent.
- All data aggregated and anonymized for compliance.

---

## 8. Data Freshness & Cadence
- HR core data refresh daily; payroll cost monthly post close.
- Turnover and absenteeism metrics recalculated nightly.
- Historical depth: 36 months for cohort analysis.
- Data Owner: HR Controlling; Technical Owner: People Analytics.

---

## 9. Edge Cases & QA Rules
- Headcount and FTE cannot be negative.
- Turnover % capped at [0; 100].
- Cross-check Revenue per FTE with Finance totals.
- Referential integrity >= 99.9 % across Date/Org.
- Privacy compliance per GDPR (no individual-level display).

---

## 10. Minimum Viable Dataset (MVD)
- Required: Headcount (FTE, hire/leave dates) + revenue/gross margin per org.
- Optional: Engagement, absenteeism, personnel cost breakdown.
- Extended: Productivity at task level, workforce planning scenarios.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Identify and address high-turnover departments | C1 | Turnover -3-5 pp; retention improves |
| Optimize workforce mix (perm/temp) based on productivity | SP1 | Personnel Cost -2-4 % |
| Link bonus pools to productivity KPIs | O2 | Revenue per FTE improves; engagement improves |
| Launch engagement or wellbeing programs | D1 | Absenteeism reduces; retention improves |
| Automate HR analytics in S&OP and budgeting | O3 | Planning accuracy improves; latency reduces |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Productivity | +5-10 % Revenue per FTE | vs Prior Year |
| Cost Efficiency | Personnel Cost Ratio -2-4 % | vs Plan |
| Retention | Turnover -3-5 pp | vs baseline |

---

## 13. Related Processes
Workforce Planning -> Budgeting & Forecasting -> Talent Management -> Engagement & Wellbeing -> HR Analytics.

---

## 14. Insights & Learnings
Turnover spikes are typically preceded by a 10 % drop in engagement scores and 15 % rise in absenteeism. Regions with balanced contract mix (70 % permanent / 30 % flex) show the best revenue per FTE.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-004 Strategic KPI Dashboard](../COR-004_Strategic_KPI_Dashboard/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
- Related Documents:  
  [`KPI Catalog`](../../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../../_includes/ActionCodes.md) | [`Glossary`](../../../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of comments] |

---

_Last updated: 04.11.2025_
