---
id: "{PREFIX}-000"
title: "[Insert Use Case Title]"
domain: "[Insert Cluster Name: Commercial / Operational Efficiency / Customer and Market / Corporate and Strategy]"
owner: "[Insert Business Owner or Responsible Department]"
impact: "[High / Medium / Low]"
status: "[Draft / In Review / Active / Deprecated]"
last_update: "DD.MM.YYYY"
---

# [Use Case Title]
Short, descriptive title summarizing the analytical question (e.g., "Sales Performance vs Plan & Last Year").

## 1. Business Goal
Explain in one to two sentences why this analysis is important for business steering or decision-making.

## 2. Business Context
Provide concise background information describing:
- The underlying business challenge or opportunity.
- The key decisions supported by this analysis.
- Dependencies such as planning cycles, data cadence, or linked processes.

## 3. Key Questions
List the guiding analytical questions this use case addresses:
- What happened?
- Where did it happen?
- Why did it happen?
- What should we do next?

## 4. Key KPIs
Each KPI must exist in the shared KPI Catalog (`/_includes/KPI_Catalog.md`).

| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| [KPI Name] | [Brief definition or formula] | [€, %, pcs, days] | [Format, e.g., 0–2 decimals] |
| [Δ KPI Name] | [Variance vs Plan or LY] | [€, %, pcs, days] | [Δ or Δ% notation] |

## 5. Typical Actions
List 3–5 operational levers or actions derived from this analysis.
Reference standardized Action Codes (`/_includes/ActionCodes.md`).

| Action | Code | Expected Effect |
|---------|------|-----------------|
| [Describe action briefly] | [P2 / D1 / W1 ...] | [e.g., GM% +1–2 pp, DSO −5 days] |

## 6. Expected Business Impact
Quantify or qualify the expected business improvement.

| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2–5 pp Δ% Net Sales | vs Plan |
| Profitability | +0.5–1 pp Gross Margin % | vs LY |
| Liquidity | DSO −5 days | vs Prior Quarter |

## 7. Related Processes
List linked processes or organizational areas that are influenced by or provide input for this analysis.

## 8. Insights & Learnings
Summarize recurring insights or findings observed during the analysis.

## 9. Cross-References
- Related Use Cases: link to sibling files within the same cluster folder.
- Related Documents: [`KPI Catalog`](../_includes/KPI_Catalog.md), [`Action Codes`](../_includes/ActionCodes.md), [`Glossary`](../_includes/Glossary.md)

## 10. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of review or comments] |

<!--
USAGE NOTES
- Replace {PREFIX} with your 3-letter cluster code (e.g., COM, OPS, CST, COR).
- File name pattern: {PREFIX}-NNN_Short_Title.md (e.g., COM-001_Sales_Performance.md)
- Place this file under the appropriate cluster folder (e.g., /usecases/01_Commercial/).
-->
