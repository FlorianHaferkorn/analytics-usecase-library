---
id: "{PREFIX}-000"
title: "[Insert Use Case Title]"
domain: "[Insert Cluster Name: Commercial / Operational Efficiency / Customer and Market / Corporate and Strategy]"
cluster: "[Insert Sub-Domain or Topic, e.g., Sales & Revenue, Supply Chain, Finance]"
reporting_level: "[Strategic / Tactical / Operational]"
analytics_stage: "[Descriptive / Diagnostic / Predictive / Prescriptive]"
owner: "[Insert Business Owner or Responsible Department]"
impact: "[High / Medium / Low]"
status: "[Draft / In Review / Active / Deprecated]"
last_update: "DD.MM.YYYY"
---

# [Use Case Title]
Short, descriptive title summarizing the analytical question (e.g., "Sales Performance vs Plan & Last Year").

---

## 1. Business Goal
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
Each KPI must exist in the shared KPI Catalog (`/_includes/KPI_Catalog.md`).

| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| [KPI Name] | [Brief definition or formula] | [€, %, pcs, days] | [Format, e.g., 0–2 decimals] |
| [Δ KPI Name] | [Variance vs Plan or LY] | [€, %, pcs, days] | [Δ or Δ% notation] |

> Naming rules:
> - Δ = absolute variance  
> - Δ% = relative variance  
> - % suffix for percentages  
> - Amount = currency; Qty = quantity; Count = integer

---

## 5. Required Attributes (Business-Level)
List the minimum fields that must be available for this use case to function.

- Date (transaction date)  
- Org (store/region)  
- Product (name/category)  
- Channel (sales channel or customer type)  
- Net Sales Amount, Units Qty  
- Optional: Promotion Flag/Type, List Price Amount

> Purpose: clarifies which business-level attributes are required for dataset mapping.

---

## 6. Segmentation & Hierarchies
Define the main dimensions and hierarchies used for analysis.

- Org: Region > Area > Store  
- Product: Category > Subcategory > SKU  
- Channel: Online / Offline / Partner  
- Time: Year > Month > Day

> These define the 30-second layer (ranking and trend analysis).

---

## 7. Scope & Assumptions
Document key assumptions and analytical boundaries.

- Sales = invoice-line granularity, returns excluded from Net Sales  
- Reporting currency = EUR; FX rate at transaction date  
- Plan version = current board-approved plan  
- Actuals = validated monthly close data  
- Time zone = Europe/Berlin

> This section prevents KPI drift and misunderstanding of calculation logic.

---

## 8. Data Freshness & Cadence
Define expected refresh behavior and latency.

- Data source refresh: daily at 06:00 CET  
- Latency ≤ 24h  
- Historical backfill = 90 days  
- Ownership: [System / Team responsible]

> Transparency for business users and data engineers.

---

## 9. Edge Cases & QA Rules
List known exceptions and quality gates before publishing.

- No negative Net Sales Amount (except return flows)  
- Percentages bounded (e.g., Price Realization % ∈ [0%; 150%])  
- Referential integrity ≥ 99.9 % across Date/Org/Product  
- All Plan versions validated and frozen before publication  
- Missing dimension members must default to "Unknown"

> These checks are part of the Definition of Done (DoD).

---

## 10. Minimum Viable Dataset (MVD)
Define the minimum data fields required to launch a basic version of this use case.

- Date, Org, Product, Net Sales Amount, Units Qty  
- Optional: Plan Amount, Last Year Amount  
- Extend with Promo Type, List Price, Margin data for advanced version

> Ensures early prototyping and incremental enrichment.

---

## 11. Typical Actions
List 3–5 operational levers or actions derived from this analysis.  
Reference standardized Action Codes (`/_includes/ActionCodes.md`).

| Action | Code | Expected Effect |
|---------|------|-----------------|
| [Describe action briefly] | [P2 / D1 / W1 ...] | [e.g., GM% +1–2 pp, DSO −5 days] |

> Example: Tighten Discounts (P2) – reduce leakage; Promo Calendar Optimization (D1) – improve forecast accuracy.

---

## 12. Expected Business Impact
Quantify or qualify the expected business improvement.

| Dimension | Expected Impact | Measurement |
|------------|-----------------|--------------|
| Revenue | +2–5 pp Δ% Net Sales | vs Plan |
| Profitability | +0.5–1 pp Gross Margin % | vs LY |
| Liquidity | DSO −5 days | vs Prior Quarter |

> Keep this section measurable and realistic.

---

## 13. Related Processes
List linked processes or organizational areas that are influenced by or provide input for this analysis.

> Example: Sales Planning, Promotion Management, Procurement, Replenishment, Forecasting.

---

## 14. Insights & Learnings
Summarize recurring insights or findings observed during the analysis.

> Example: Price Realization correlates more strongly with Gross Margin % than Volume Growth in non-promo periods.

---

## 15. Cross-References
Provide links to related use cases or documentation.

- **Related Use Cases:**  
  `[{{PREFIX}}-002 Related Use Case](../<ClusterFolder>/{{PREFIX}}-002_Example.md)`  

- **Related Documents:**  
  [`Reporting Strategy`](../docs/Reporting_Strategy.md)  
  [`Methodology`](../docs/Methodology.md)  
  [`KPI Catalog`](../_includes/KPI_Catalog.md)  
  [`Action Codes`](../_includes/ActionCodes.md)  
  [`Glossary`](../_includes/Glossary.md)

---

## 16. Review Information
| Field | Value |
|--------|--------|
| Business Reviewer | [Name / Role] |
| Technical Reviewer | [Name / Role] |
| Version | v1.0 |
| Review Date | DD.MM.YYYY |
| Review Notes | [Summary of review or comments] |

---

_Last updated: DD.MM.YYYY_

---

<!--
USAGE NOTES
- Replace {PREFIX} with your 3-letter cluster code (e.g., COM, OPS, CST, COR).
- Add reporting_level and analytics_stage according to the Reporting Strategy.
- File name pattern: {PREFIX}-NNN_Short_Title.md (e.g., COM-001_Sales_Performance.md)
- Place this file under the appropriate cluster folder (e.g., /usecases/01_Commercial/).
-->
