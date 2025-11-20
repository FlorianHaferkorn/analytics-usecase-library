---
id: "COR-004"
title: "Strategic KPI Dashboard (Enterprise Performance Overview)"
domain: "Corporate and Strategy"
owner: "Executive Board / Strategy Office"
impact: "Very High"
status: "Draft"
last_update: "04.11.2025"
maturity: "Pilot"
reporting_level: "Strategic"
analytics_stage: "Descriptive"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Cash Conversion Cycle", "ESG-Aligned Revenue %", "Turnover %", "Project ROI %"]
supports_strategic_kpi_ids: ["sales.revenue.growth_pct", "margin.gm.pct", "ops.working_capital.ccc.days", "esg.aligned_revenue.pct", "hr.turnover.pct", "corp.project.roi.pct"]
action_codes: ["SP2", "O2", "SP1", "O3", "SP3"]
expected_impact: "Unified view of top KPIs; -50 % latency from data to decision; +100 % KPI-goal linkage"
dataset_model: "Contoso Sales Sample for Power BI Desktop.SemanticModel"
page_template: "overview_drivers_details"
segments: [
  "Org.Region>BusinessUnit",
  "KPI.Domain>Sub-Domain",
  "Time.Year>Quarter>Month"
]
filters_default: [
  "Time: Last 12M",
  "Domain: All",
  "Org: All"
]
qa_asserts: ["RI_OK", "KPI_Source_Registered", "Plan_Actual_Alignment"]
required_kpi_ids: [
  "sales.net_sales.delta_pct.ly",
  "margin.gm.pct",
  "ops.working_capital.ccc.days",
  "hr.turnover.pct",
  "esg.aligned_revenue.pct",
  "corp.project.roi.pct"
]
required_kpis:
  sales.net_sales.delta_pct.ly: "Δ% Net Sales"
  margin.gm.pct: "Gross Margin %"
  ops.working_capital.ccc.days: "Cash Conversion Cycle (Days)"
  hr.turnover.pct: "Turnover Rate %"
  esg.aligned_revenue.pct: "ESG-Aligned Revenue %"
  corp.project.roi.pct: "Project ROI %"
data_requirements:
  facts:
    - name: fact_kpi_scores
      grain: kpi_org_month
      primary_key: [KpiID, OrgID, Month]
      required_columns:
        - { name: KpiID, type: string, role: attribute }
        - { name: OrgID, type: string, role: org_key }
        - { name: Month, type: date, role: date_key }
        - { name: Domain, type: string, role: attribute }
        - { name: ActualValue, type: decimal, role: amount }
        - { name: PlanValue, type: decimal, role: amount }
        - { name: TargetValue, type: decimal, role: amount }
        - { name: Status, type: string, role: status }
        - { name: Owner, type: string, role: attribute }
        - { name: Commentary, type: string, role: text }
    - name: fact_initiatives
      grain: initiative
      primary_key: [InitiativeID]
      required_columns:
        - { name: InitiativeName, type: string, role: attribute }
        - { name: LinkedKpiID, type: string, role: attribute }
        - { name: Status, type: string, role: status }
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
    - name: dim_kpi
      grain: kpi
      primary_key: [KpiID]
      required_columns:
        - { name: KPIName, type: string }
        - { name: Domain, type: string }
        - { name: SourceUseCase, type: string }
        - { name: Frequency, type: string }
  relationships:
    - { from: fact_kpi_scores.OrgID, to: dim_org.OrgID, cardinality: many-to-one, direction: single }
    - { from: fact_kpi_scores.Month, to: dim_date.Date, cardinality: many-to-one, direction: single }
    - { from: fact_kpi_scores.KpiID, to: dim_kpi.KpiID, cardinality: many-to-one, direction: single }
    - { from: fact_initiatives.LinkedKpiID, to: dim_kpi.KpiID, cardinality: many-to-one, direction: single }
model_mapping:
  "Actual Value": "fact_kpi_scores[ActualValue]"
  "Plan Value": "fact_kpi_scores[PlanValue]"
  "Target Value": "fact_kpi_scores[TargetValue]"
  "Status": "fact_kpi_scores[Status]"
  "Owner": "fact_kpi_scores[Owner]"
  "Commentary": "fact_kpi_scores[Commentary]"
  "KPI Name": "dim_kpi[KPIName]"
  "Domain": "dim_kpi[Domain]"
  "Source Use Case": "dim_kpi[SourceUseCase]"
  "Org": "dim_org[OrgID]"
  "Date": "dim_date[Date]"
---

# Strategic KPI Dashboard (Enterprise Performance Overview)

## 1. Business Goal
Provide a single, consolidated view of strategic KPIs across all business domains - enabling leadership to monitor execution of corporate strategy, track key objectives, and steer actions based on real-time insights.

---

## 2. Business Context
Executive teams often receive dozens of disconnected dashboards. Decisions slow down because KPIs have inconsistent definitions, plan versions, or owners. This strategic dashboard enforces a canonical KPI registry linked to each domain use case. It aligns finance, operations, people, and sustainability KPIs on one page, highlights gap-to-target, and traces every KPI back to accountable owners and initiatives.

---

## 3. Key Questions
- Are we on track to achieve corporate strategic and financial targets?
- Which business domains drive value creation or risk?
- How do operational, financial, and ESG metrics correlate?
- Where are emerging risks or opportunities across the portfolio?
- What trends require strategic intervention?

---

## 4. Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Δ% Net Sales | (Net Sales - LY) / LY | % | +/- with 1 decimal |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % | 1 decimal |
| Cash Conversion Cycle | DSO + DIO - DPO | days | 0 decimals |
| Turnover Rate % | Exits / Average headcount | % | 1 decimal |
| ESG-Aligned Revenue % | Taxonomy-aligned revenue / Total revenue | % | 1 decimal |
| Project ROI % | (Realized Benefit - Cost) / Cost | % | 1 decimal |

---

## 5. Required Attributes (Business-Level)
- Date (month-end or quarter-end)
- Org (company, region, business unit)
- Domain Source (Commercial, Operations, People, ESG, Strategy)
- Actual, Plan, Forecast, and Target Values per KPI
- Optional: Owner, Status (On Track / At Risk / Off Track), Commentary

---

## 6. Segmentation & Hierarchies
- Org: Region > Business Unit > Entity
- Domain: Commercial / Operations / People / ESG / Strategy
- KPI Type: Financial / Operational / ESG / People
- Time: Year > Quarter > Month
- Initiative: Program > Project (links to Use Cases)

---

## 7. Scope & Assumptions
- KPIs sourced from validated domain models (semantic layer).
- Actuals vs Plan harmonized per fiscal calendar (May-April).
- Each KPI has an assigned owner and update frequency.
- Currency = EUR; consolidated at Group Level.
- Refresh and validation aligned with monthly performance reviews.

---

## 8. Data Freshness & Cadence
- Core KPIs refresh daily (finance/operations) with weekly executive snapshots; strategic scoreboard locked post month-end close.
- KPI metadata (owner, thresholds) maintained centrally via KPI registry.
- Data Owner: Strategy Office; Technical Owner: Enterprise BI.

---

## 9. Edge Cases & QA Rules
- KPI source must reference a validated Use Case ID.
- Actual/Plan mismatch flagged automatically.
- Missing commentary for 'Off Track' KPIs prohibited.
- Referential integrity >= 99.9 % across Date/Org/KPI.
- Audit trail required for changes in KPI definitions.

---

## 10. Minimum Viable Dataset (MVD)
- Required: KPI registry (ID, owner, source) + actual/plan/target per KPI/org/time.
- Optional: Linked initiatives, risk ratings, commentary workflow.
- Extended: Predictive forecasts, AI-generated narratives, scenario tags.

---

## 11. Typical Actions
| Action | Code | Expected Effect |
|---------|------|-----------------|
| Review and reprioritize initiatives in underperforming domains | SP2 | ROI improves; performance gap reduces |
| Launch strategic interventions for KPIs 'Off Track' | O2 | Execution speed improves; deviation reduces |
| Link KPI ownership to management scorecards | SP1 | Accountability improves; alignment improves |
| Integrate KPI narrative automation (AI-generated summaries) | O3 | Reporting latency reduces 70 % |
| Adjust strategic targets based on rolling forecasts | SP3 | Forecast bias reduces; agility improves |

---

## 12. Expected Business Impact
| Dimension | Expected Impact | Measurement |
|------------|-----------------|-------------|
| Decision Speed | -50 % latency from data to decision | governance cycle |
| KPI Coverage | 100 % strategic KPIs linked to owners | KPI registry |
| Strategic Alignment | +100 % KPI-goal linkage | board scorecard |

---

## 13. Related Processes
Enterprise Performance Management -> Board Reporting -> Strategic Planning -> Financial Forecasting -> BI Governance.

---

## 14. Insights & Learnings
Consolidating KPIs into a single registry cut manual board prep time by half and exposed duplicate metrics. Aligning KPI commentary with action codes ensures the board focuses on decision-ready insights rather than data disputes.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../COR-001_Project_ROI_and_Benefit_Tracking/FactSheet.md)`  
  `[COR-002 Workforce Productivity & Turnover](../COR-002_Workforce_Productivity_and_Turnover/FactSheet.md)`  
  `[COR-003 ESG & Compliance Monitoring](../COR-003_ESG_and_Compliance_Monitoring/FactSheet.md)`  
  `[COM-001 Sales Performance](../../01_Commercial/COM-001_Sales_Performance/FactSheet.md)`  
  `[OPS-001 Cash Conversion Cycle](../../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle/FactSheet.md)`  
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
