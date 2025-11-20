---
id: "COR-001"
title: "Project ROI & Benefit Tracking"
domain: "Corporate and Strategy"
owner: "Head of Strategy / PMO / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Tactical"
analytics_stage: "Diagnostic"
supports_strategic_kpi: ["Project ROI %", "Benefit Realization %", "Operating Cost Ratio %"]
supports_strategic_kpi_ids: ["corp.project.roi.pct", "corp.benefit.realization.pct", "corp.payback.months"]
action_codes: ["SP1", "SP2", "O2", "O3", "SP3"]
expected_impact: "+5-10 pp realized ROI; +15 % benefit realization; -10-20 % manual reporting effort"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Portfolio.Pillar>Program>Project",
  "Org.Region>BusinessUnit",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Portfolio: All",
  "Stage: All"
]
qa_asserts: ["RI_OK", "Benefit_Not_Negative", "ROI_InRange"]
required_kpi_ids: [
  "corp.project.roi.pct",
  "corp.benefit.realization.pct",
  "corp.budget.adherence.pct",
  "corp.schedule.adherence.pct",
  "corp.payback.months"
]
required_kpis:
  corp.project.roi.pct: "Project ROI %"
  corp.benefit.realization.pct: "Benefit Realization %"
  corp.budget.adherence.pct: "Budget Adherence %"
  corp.schedule.adherence.pct: "Schedule Adherence %"
  corp.payback.months: "Payback Period (Months)"
data_requirements:
  facts:
    - name: fact_projects
      grain: project_month
      primary_key: [ProjectID, SnapshotMonth]
      required_columns:
        - { name: ProjectID, type: string, role: project_key }
        - { name: SnapshotMonth, type: date, role: date_key }
        - { name: Portfolio, type: string, role: attribute }
        - { name: Pillar, type: string, role: attribute }
        - { name: Stage, type: string, role: status }
        - { name: PlannedCost, type: decimal, role: amount }
        - { name: ActualCost, type: decimal, role: amount }
        - { name: PlannedBenefit, type: decimal, role: amount }
        - { name: RealizedBenefit, type: decimal, role: amount }
        - { name: ExpectedPaybackMonths, type: decimal, role: helper }
        - { name: ScheduleProgressPct, type: decimal, role: helper }
    - name: fact_project_actions
      grain: action
      primary_key: [ProjectID, ActionID]
      required_columns:
        - { name: ActionDate, type: date, role: date_key }
        - { name: ActionType, type: string, role: attribute }
        - { name: Owner, type: string, role: attribute }
  dims:
    - name: dim_project
      grain: project
      primary_key: [ProjectID]
      required_columns:
        - { name: ProjectName, type: string }
        - { name: Sponsor, type: string }
        - { name: BusinessOwner, type: string }
        - { name: CapexOpexFlag, type: string }
        - { name: RiskLevel, type: string }
    - name: dim_org
      grain: org
      primary_key: [OrgID]
    - name: dim_date
      grain: date
      primary_key: [Date]
  relationships:
    - { from: fact_projects.ProjectID, to: dim_project.ProjectID, cardinality: many-to-one, direction: single }
    - { from: fact_projects.SnapshotMonth, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_project_actions.ProjectID, to: dim_project.ProjectID, cardinality: many-to-one, direction: single }
model_mapping:
  "Project": "dim_project[ProjectName]"
  "Portfolio": "fact_projects[Portfolio]"
  "Pillar": "fact_projects[Pillar]"
  "Stage": "fact_projects[Stage]"
  "Planned Cost": "fact_projects[PlannedCost]"
  "Actual Cost": "fact_projects[ActualCost]"
  "Planned Benefit": "fact_projects[PlannedBenefit]"
  "Realized Benefit": "fact_projects[RealizedBenefit]"
  "Schedule Progress %": "fact_projects[ScheduleProgressPct]"
  "Snapshot Month": "fact_projects[SnapshotMonth]"
---

# Project ROI & Benefit Tracking

## 1. Business Goal
Ensure transparency on project performance by tracking realized financial and non-financial benefits versus investment cost - enabling data-driven portfolio steering, reprioritization, and early escalation.

---

## 2. Business Context
Strategy teams often approve dozens of initiatives without a consistent way to monitor whether benefits materialize. Financial controllers receive updates in spreadsheets, making it hard to reconcile CapEx, OpEx, and realized savings or revenue. This use case replaces manual PMO decks with a live cockpit that combines investment, delivery, and benefit signals. It supports steering committees with a standardized ROI story so capital can be reallocated quickly and underperforming projects can be stopped before sunk-cost escalation occurs.

---

## 3. Key Questions
- What is the realized ROI per project and portfolio segment?
- Are projects delivering expected benefits on time and within budget?
- Which initiatives drive the highest strategic and financial impact?
- What portion of planned savings or revenue uplift is actually realized?
- How do project delays correlate with ROI erosion?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Project ROI % | (Realized Benefit - Actual Cost) / Actual Cost | % | 1 decimal |
| Benefit Realization % | Realized Benefit / Planned Benefit | % | 1 decimal |
| Budget Adherence % | Actual Cost / Planned Cost | % | 1 decimal |
| Schedule Adherence % | Actual progress vs planned milestones | % | 1 decimal |
| Payback Period (Months) | Months to cumulative breakeven | months | 0 decimals |

---

## 5. Required Attributes (Business-Level)
- Project ID, Project Name, Portfolio, Strategic Pillar
- Planned Cost, Actual Cost, Planned Benefits, Realized Benefits
- Start Date, End Date, Stage (Initiation/Execution/Closed)
- Optional: Sponsor, Project Type (CapEx/OpEx), Currency, Risk Level

---

## 6. Segmentation & Hierarchies
- Portfolio: Pillar > Program > Project
- Org: Region > Business Unit > Cost Center
- Stage: Initiate > Plan > Execute > Close
- Benefit Type: Revenue / Cost / Non-financial
- Time: Year > Quarter > Month

---

## 7. Scope & Assumptions
- Project ROI considers all CapEx + OpEx vs realized financial benefit.
- Benefits captured when measurable in P&L (not forecast only).
- Non-financial KPIs (e.g., CX, ESG) optionally tracked as qualitative.
- Currency = EUR; FX rate at commitment date.
- ROI target benchmark typically >= 15 %.

---

## 8. Data Freshness & Cadence
- Project financials refresh weekly from ERP/PPM; benefit registers daily where automated.
- Status updates aligned with PMO cadence (bi-weekly or monthly).
- Historical depth: full project history + 24 months after closure for benefit tracking.
- Data Owner: PMO; Technical Owner: Corporate BI.

---

## 9. Edge Cases & QA Rules
- Projects with ROI < -100 % flagged 'Loss-Making'.
- Benefit > Planned x 1.5 flagged for review (potential misallocation).
- Project without closure date cannot report realized benefits.
- Referential integrity >= 99.9 % across Project/Org/Time.
- Status updates must align with PMO governance cadence.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Project master (ID, stage, dates) + cost and benefit actuals.
- Optional: Risk assessments, qualitative KPIs, owner details.
- Extended: Scenario ROI, dependency mapping, resource consumption.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Reassess project scope or timeline if ROI < threshold | SP1 | ROI improves; delay reduces |
| Prioritize or divest projects based on realized ROI ranking | SP2 | Portfolio efficiency improves |
| Enforce benefit owner accountability | O2 | Benefit Realization % +10-15 pp |
| Introduce stage-gate reviews for high-risk projects | O3 | Risk exposure reduces; predictability improves |
| Link PMO bonus targets to benefit realization | SP3 | ROI target compliance improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Benefit Realization | +15 % realized vs plan | vs Plan |
| ROI | +5-10 pp ROI for top quartile | vs Prior Year |
| Reporting Efficiency | -10-20 % manual effort | time spent |

---

## 13. Related Processes
Portfolio Management -> Strategic Planning -> Financial Forecasting -> PMO Governance -> CapEx Planning.

---

## 14. Insights & Learnings
Projects with clear benefit owners and monthly benefit validation achieve 1.5x higher realization. Early-stage schedule slippage is the leading indicator for cost overruns and payback delays.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-002 Workforce Productivity & Turnover](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[COM-002 Gross Margin Analysis](../../01_Commercial/COM-002_Gross_Margin_Analysis/FactSheet.md)`  
  `[OPS-003 Purchase Price Variance](../../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance/FactSheet.md)`  
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
