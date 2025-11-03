---
id: "COR-001"
title: "Project ROI & Benefit Tracking"
domain: "Corporate and Strategy"
owner: "Head of Strategy / PMO / Finance Controlling"
impact: "High"
status: "Draft"
last_update: "07.10.2025"
supports_strategic_kpi: ["Project ROI %", "Benefit Realization %", "Operating Cost Ratio %"]
action_codes: ["SP1", "SP2", "O2", "O3", "SP3"]
expected_impact: "+5-10 pp realized ROI; +15 % benefit realization; -10-20 % manual reporting effort"
---

# Project ROI & Benefit Tracking

## 1. Business Goal
Ensure transparency on project performance by tracking realized financial and non-financial benefits versus investment cost — enabling data-driven portfolio steering, reprioritization, and early escalation.

---

## 2. Business Context
Organizations execute numerous initiatives across digital, operational, and strategic domains.  
Many fail to deliver expected ROI due to scope drift, delayed realization, or untracked benefits.  
This use case provides a standardized structure to measure project ROI, benefit realization, and alignment to strategic objectives.  
It links finance (CapEx/OpEx), delivery (timeline/milestones), and value realization (P&L impact).

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
| Project ROI % | (Realized Benefits - Total Cost) / Total Cost | % | 1 decimal |
| Benefit Realization % | Realized Benefits / Planned Benefits | % | 1 decimal |
| Budget Adherence % | Actual Cost / Planned Cost | % | 1 decimal |
| Schedule Adherence % | Actual Progress / Planned Progress | % | 1 decimal |
| Payback Period | Time until cumulative benefits = total cost | Months | 0 decimals |

---

## 5. Required Attributes (Business-Level)
- Project ID, Project Name, Portfolio, Strategic Pillar  
- Planned Cost, Actual Cost, Planned Benefits, Realized Benefits  
- Start Date, End Date, Stage (Initiation/Execution/Closed)  
- Optional: Sponsor, Project Type (CapEx/OpEx), Currency, Risk Level  

---

## 6. Segmentation & Hierarchies
- Portfolio: Strategic Pillar > Program > Project  
- Org: Corporate > Region > Department  
- Time: Year > Quarter > Month  
- Project Stage: Initiation > Execution > Closure  

---

## 7. Scope & Assumptions
- Project ROI considers all CapEx + OpEx vs realized financial benefit.  
- Benefits captured when measurable in P&L (not forecast only).  
- Non-financial KPIs (e.g., CX, ESG) optionally tracked as qualitative.  
- Currency = EUR; FX rate at commitment date.  
- ROI target benchmark typically >= 15 %.  

---

## 8. Data Freshness & Cadence
- Refresh: monthly (5th business day after close).  
- Latency <= 72h post-close.  
- Historical depth = project duration + 12 months post-closing.  
- Data Owner: PMO / Finance Controlling.  

---

## 9. Edge Cases & QA Rules
- Projects with ROI < -100 % flagged 'Loss-Making'.  
- Benefit > Planned × 1.5 flagged for review (potential misallocation).  
- Project without closure date cannot report realized benefits.  
- Referential integrity >= 99.9 % across Project/Org/Time.  
- Status updates must align with PMO governance cadence.

---

## 10. Minimum Viable Dataset (MVD)
- Required: Project ID, Planned Cost, Actual Cost, Planned Benefit, Realized Benefit.  
- Optional: Stage, Sponsor, Start/End Date.  
- Extended: Portfolio, Strategic Pillar, Non-Financial KPIs, Risk Rating.

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
|------------|-----------------|--------------|
| ROI | +5-10 pp improvement in realized ROI | vs LY |
| Benefit Realization | +15 % realization rate | portfolio average |
| Portfolio Efficiency | +10-20 % higher value per EUR invested | rolling 12M |

---

## 13. Related Processes
Portfolio Management · Strategic Planning · Financial Forecasting · PMO Governance · CapEx Planning.

---

## 14. Insights & Learnings
Benefit realization is most successful when ownership is assigned at initiation — not after go-live.  
ROI gaps usually stem from delayed benefit tracking, not overspending.  
Linking PMO dashboards with Finance ensures credibility and faster corrective actions.

---

## 15. Cross-References
- Related Use Cases:  
  `[COR-002 Workforce Productivity & Turnover](../04_Corporate_and_Strategy/COR-002_Workforce_Productivity_and_Turnover.md)`  
  `[COM-002 Gross Margin Analysis](../01_Commercial/COM-002_Gross_Margin_Analysis.md)`  
  `[OPS-003 Purchase Price Variance](../02_Operational_Efficiency/OPS-003_Purchase_Price_Variance.md)`  
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
