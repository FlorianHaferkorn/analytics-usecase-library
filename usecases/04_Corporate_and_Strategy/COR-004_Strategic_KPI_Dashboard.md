---
id: "COR-004"
title: "Strategic KPI Dashboard (Enterprise Performance Overview)"
domain: "Corporate and Strategy"
owner: "Executive Board / Strategy Office"
impact: "Very High"
status: "Draft"
last_update: "07.10.2025"
supports_strategic_kpi: ["Revenue Growth %", "Gross Margin %", "Cash Conversion Cycle", "ESG-Aligned Revenue %", "Turnover %", "Project ROI %"]
action_codes: ["SP2", "O2", "SP1", "O3", "SP3"]
expected_impact: "Unified view of top KPIs; -50 % latency from data to decision; +100 % KPI-goal linkage"
---

# Strategic KPI Dashboard (Enterprise Performance Overview)

## 1. Business Goal
Provide a single, consolidated view of strategic KPIs across all business domains — enabling leadership to monitor execution of corporate strategy, track key objectives, and steer actions based on real-time insights.

---

## 2. Business Context
Executives need an integrated, forward-looking performance cockpit that combines financial, operational, people, and sustainability metrics.  
Traditional reports are siloed by function and time-delayed.  
This use case defines the top-level KPI structure for enterprise-wide performance management, ensuring alignment between strategic targets and operational reality.

---

## 3. Key Questions
- Are we on track to achieve corporate strategic and financial targets?  
- Which business domains drive value creation or risk?  
- How do operational, financial, and ESG metrics correlate?  
- Where are emerging risks or opportunities across the portfolio?  
- What trends require strategic intervention?

---

## 4. Key KPIs (Top-Level)
| KPI | Definition | Unit | Source |
|------|-------------|------|--------|
| Δ% Net Sales | (Actual - Plan) / Plan | % | COM-001 |
| Gross Margin % | (Net Sales - COGS) / Net Sales | % | COM-002 |
| Cash Conversion Cycle | DSO + DIO - DPO | Days | OPS-001 |
| Employee Turnover % | Leavers / Avg Headcount | % | COR-002 |
| ESG-Aligned Revenue % | Revenue meeting EU Taxonomy | % | COR-003 |
| Project ROI % | (Realized Benefit - Cost) / Cost | % | COR-001 |

---

## 5. Required Attributes (Business-Level)
- Date (month-end or quarter-end)  
- Org (company, region, business unit)  
- Domain Source (Commercial, Operations, People, ESG, Strategy)  
- Actual, Plan, Forecast, and Target Values per KPI  
- Optional: Owner, Status (On Track / At Risk / Off Track), Commentary  

---

## 6. Segmentation & Hierarchies
- Org: Corporate > Region > Business Unit > Department  
- Domain: Commercial / Operational / People / ESG / Strategy  
- Time: Year > Quarter > Month  
- KPI Type: Financial / Operational / Strategic / ESG  

---

## 7. Scope & Assumptions
- KPIs sourced from validated domain models (semantic layer).  
- Actuals vs Plan harmonized per fiscal calendar (May–April).  
- Each KPI has an assigned owner and update frequency.  
- Currency = EUR; consolidated at Group Level.  
- Refresh and validation aligned with monthly performance reviews.

---

## 8. Data Freshness & Cadence
- Refresh: daily for actuals, monthly for full consolidation.  
- Latency <= 24h (automated pipelines).  
- Historical depth = 60 months (5 fiscal years).  
- Data Owner: Strategy Office / BI Governance.

---

## 9. Edge Cases & QA Rules
- KPI source must reference a validated Use Case ID.  
- Actual/Plan mismatch flagged automatically.  
- Missing commentary for 'Off Track' KPIs prohibited.  
- Referential integrity >= 99.9 % across Date/Org/KPI.  
- Audit trail required for changes in KPI definitions.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Date, Org, KPI ID, Actual, Plan, Target.  
- Optional: Forecast, Status, Owner.  
- Extended: Commentary, Link to Action Plan, Trend Classification.

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
|------------|-----------------|--------------|
| Transparency | Unified view of 100 % top KPIs | group-wide |
| Decision Speed | -50 % latency from data to decision | vs baseline |
| Strategic Alignment | 100 % of KPIs linked to corporate goals | governance metric |
| Reporting Efficiency | -60 % manual effort | vs previous process |

---

## 13. Related Processes
Enterprise Performance Management · Board Reporting · Strategic Planning · Financial Forecasting · BI Governance.

---

## 14. Insights & Learnings
The highest impact of strategy execution comes from transparency and cadence — not the number of metrics.  
KPIs must remain stable but interpretations adaptive.  
A living 'one source of truth' across all domains accelerates management alignment and trust in data.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-001 Project ROI & Benefit Tracking](../04_Corporate_and_Strategy/COR-001_Project_ROI_and_Benefit_Tracking.md)`  
  `[COR-002 Workforce Productivity & Turnover](../04_Corporate_and_Strategy/COR-002_Workforce_Productivity_and_Turnover.md)`  
  `[COR-003 ESG & Compliance Monitoring](../04_Corporate_and_Strategy/COR-003_ESG_and_Compliance_Monitoring.md)`  
  `[COM-001 Sales Performance](../01_Commercial/COM-001_Sales_Performance.md)`  
  `[OPS-001 Cash Conversion Cycle](../02_Operational_Efficiency/OPS-001_Cash_Conversion_Cycle.md)`  
- Related Documents:  
  [`KPI Catalog`](../../_includes/kpi_catalog/README.md) | [`Action Codes`](../../_includes/ActionCodes.md) | [`Glossary`](../../_includes/Glossary.md)

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

_Last updated: 07.10.2025_
