---
id: {PREFIX}-000
title: [Insert Use Case Title]
domain: [Insert Cluster Name, e.g., Commercial / Operational Efficiency / Customer and Market / Corporate and Strategy]
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
Provide concise background information describing:  
- The underlying business challenge or opportunity.  
- The key decisions supported by this analysis.  
- Dependencies such as planning cycles, data cadence, or linked processes.  

> Example: Sales deviations drive liquidity and profitability. This use case highlights where and why deviations occur and provides actionable levers.

---

## 3. Key Questions
List the guiding analytical questions this use case addresses:  

- What happened?  
- Where did it happen?  
- Why did it happen?  
- What should we do next?  

> Keep these question sets consistent; they guide KPI selection and visual design.

---

## 4. Key KPIs
Define the core KPIs analyzed in this use case.  
Each KPI must exist in the shared KPI Catalog (`/_includes/KPI_Catalog.md`).

| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| [KPI Name] | [Brief definition or formula] | [€, %, pcs, days] | [Format, e.g., 0–2 decimals] |
| [Δ KPI Name] | [Variance vs Plan or LY] | [€, %, pcs, days] | [Δ or Δ% notation] |

> Use standard naming rules:  
> - Δ = absolute variance  
> - Δ% = relative variance  
> - % suffix for percentages  
> - Amount = currency; Qty = quantity; Count = integer

---

## 5. Typical Actions
List 3–5 operational levers or actions derived from this analysis.  
Each action should reference a standardized **Action Code** (`/_includes/ActionCodes.md`).

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

> Keep this section measurable and realistic. Avoid generic statements.

---

## 7. Related Processes
List linked processes or organizational areas that are influenced by or provide input for this analysis.  

> Example: Sales Planning, Promotion Management, Procurement, Replenishment, Forecasting.

---

## 8. Insights & Learnings
Summarize recurring insights or findings observed during the analysis.  
This section is updated as patterns or business learnings emerge.

> Example: Price Realization correlates more strongly with Gross Margin % than Volume Growth in non-promo periods.

---

## 9. Cross-References
Provide links to related use cases or documentation.

- **Related Use Cases:**  
  `[{{PREFIX}}-002 Related Use Case](../<ClusterFolder>/{{PREFIX}}-002_Example.md)`  

- **Related Documents:**  
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
| Review Notes | [Summary of review or comments] |

---

_Last updated: DD.MM.YYYY_
