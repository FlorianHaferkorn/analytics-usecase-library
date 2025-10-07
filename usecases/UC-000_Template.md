---
id: UC-000
title: [Insert Use Case Title]
domain: [Insert Domain or Cluster Name]
owner: [Insert Business Owner or Responsible Department]
impact: [High / Medium / Low]
status: [Draft / In Review / Active / Deprecated]
last_update: DD.MM.YYYY
---

# [Use Case Title]
*Short, descriptive title summarizing the analytical question (e.g., "Sales Performance vs Plan & Last Year").*

---

## 1. Business Goal
*Purpose:*  
Explain in one to two sentences why this analysis is important for business steering or decision-making.  
Focus on the **business outcome**, not the technical metric.  
> Example: Ensure sustainable revenue growth by identifying and explaining deviations versus Plan and Last Year.

---

## 2. Business Context
Provide a short background describing:  
- The underlying business problem or challenge.  
- The key decisions supported by this analysis.  
- Relevant dependencies (e.g., planning cycles, other reports).  
> Example: Sales deviations drive liquidity and profitability. The use case highlights where and why deviations occur.

---

## 3. Key Questions
List the guiding questions this use case should answer.  
They define the analytical intent and drive the KPI selection.

- What happened? (e.g., Where do we miss our plan?)  
- Where did it happen? (e.g., Which products, regions, or channels?)  
- Why did it happen? (e.g., Price, Volume, Mix, or external effects?)  
- What should we do next? (Link to typical actions.)

---

## 4. Key KPIs
Define the core KPIs analyzed in this use case.  
Each KPI must exist in the central KPI Catalog (`/_includes/KPI_Catalog.md`).

| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| [KPI Name] | [Brief definition or formula] | [€, %, pcs, days] | [Format, e.g. 0–2 decimals] |
| [Δ KPI Name] | [Variance vs Plan or LY] | [€, %, pcs, days] | [Δ or Δ% notation] |

> Always use the naming standards:  
> - Δ = absolute variance  
> - Δ% = relative variance  
> - % suffix for percentages

---

## 5. Typical Actions
List 3–5 concrete operational levers or actions derived from this analysis.  
Each action should refer to a standardized **Action Code** (`/_includes/ActionCodes.md`).

| Action | Code | Expected Effect |
|---------|------|-----------------|
| [Describe action briefly] | [P2 / D1 / W1 ...] | [e.g., GM% +1–2 pp, DSO −5 days] |

> Example: Tighten Discounts (P2) – reduce leakage; Promo Calendar Optimization (D1) – improve forecast accuracy.

---

## 6. Expected Business Impact
Quantify or qualify the expected business improvement.

| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2–5 pp Δ% Net Sales | vs Plan |
| Profitability | +0.5–1 pp Gross Margin % | vs LY |
| Liquidity | DSO −5 days | vs Prior Quarter |

> Keep this section measurable; avoid vague statements like “improve performance”.

---

## 7. Related Processes
List linked business processes or planning activities that influence or are influenced by this analysis.  
> Example: Sales Planning, Promotion Management, Pricing Strategy, Replenishment, Forecasting.

---

## 8. Insights & Learnings
Summarize qualitative findings or recurring patterns discovered through this analysis.  
This section is often updated after review cycles or repeated report usage.

> Example: Price Realization has stronger impact on GM % than volume growth in non-promo periods.

---

## 9. Cross-References
Link to other related use cases, glossary terms, or packages.  

- Related Use Cases:  
  `[UC-002 Gross Margin %](../01_Commercial/UC-002_Gross_Margin_Analysis.md)`  
  `[UC-015 Price-Volume-Mix Bridge](../01_Commercial/UC-015_Price_Volume_Mix_Bridge.md)`  

- Related Documents:  
  [`KPI Catalog`](../_includes/KPI_Catalog.md)  
  [`Action Codes`](../_includes/ActionCodes.md)  
  [`Glossary`](../_includes/Glossary.md)

---

## 10. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of key feedback] |

---

_Last updated: DD.MM.YYYY_
