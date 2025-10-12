# Methodology & Rationale

## 1. Framework Context
This document complements the overarching **[Reporting Strategy](./Reporting_Strategy.md)** by explaining *how* its principles are operationalized within the **Analytics Use Case Library**.  
While the Strategy defines *what* layers and levels exist, the Methodology defines *how* to implement and maintain them in daily work.

> **Purpose:** Ensure every Use Case, KPI, and report follows a coherent, governed, and reusable analytical method.

---

## 2. Standardization Philosophy
**Why standardize?**  
To reduce ambiguity, accelerate delivery, and build trust in every insight.

**Core principles:**
- Shared semantic model: conformed dimensions, reusable measures, consistent naming.  
- Separation of business logic (Markdown) and technical implementation (semantic model).  
- Reuse over reinvention: leverage existing KPIs, Action Codes, and hierarchies.  
- Documentation-first: each Use Case must be understandable without the author.  

**Benefits:**
- Faster onboarding, simpler reviews, fewer misinterpretations.  
- KPI comparability across domains and time.  
- AI/Copilot-readiness through structured metadata.

---

## 3. Reporting Design — 3-30-300 Principle
Design each report page for three reading depths:

| Layer | Purpose | Typical Visuals |
|--------|----------|-----------------|
| **3 s (Insight)** | 4–5 KPI Cards showing result + Δ | KPI Cards, Trend Arrows |
| **30 s (Story)** | Show where/when changes occur | Line for time, horizontal bar for ranking, waterfall for bridges |
| **300 s (Detail)** | Root cause analysis | Table/Matrix (drill + export), scatter (correlation), 100 % stacked bar |

**Rules:**
- ≤ 3 slicers per page; include meaningful reference lines.  
- Minimal color use; highlight only what changes.  
- Replace pie/donut charts with 100 % stacked alternatives.

**Why it matters:**  
It creates a consistent decision experience for executives (3 / 30) and analysts (300) in one structure.

---

## 4. Semantic Modeling 101
**Goal:** performance + reusability + reliability.

**Standards:**
- **Star schema** with fact tables at clear grain; conformed dimensions for cross-domain analysis.  
- **Measures over calculated columns** for performance and logic consistency.  
- **Role-playing date dimensions** for multiple time perspectives.  
- **Referential integrity ≥ 99.9 %**, surrogate keys on all dimensions.  
- **RLS/OLS** applied only on dimensions (Org, Customer, etc.).  
- **Display folders** group measures by business domain.

**Impact:** predictable DAX, easier validation, automation readiness.

---

## 5. Measure & Naming Standards
**Objectives:** readability, precision, machine interpretability.

| Type | Rule | Example |
|-------|------|----------|
| Currency | End with `Amount` | Net Sales Amount |
| Quantity | End with `Qty` | Units Qty |
| Count | End with `Count` / `Distinct Count` | Customer Count |
| % Ratio | End with `%` | Gross Margin % |
| Abs. Variance | Prefix `Δ` | Δ Net Sales Amount |
| Rel. Variance | Prefix `Δ%` | Δ% Gross Margin |
| Time Scope | Suffix `YTD / MTD / QTD / YoY / MoM` | Net Sales Amount YTD |

**Formatting:**  
Amount = 0–2 dec €, Qty/Count = integer, % = 1–2 dec.

**Display Folders (examples):**  
`01_Sales`, `02_Margin`, `04_Cash`, `05_Customer`, `08_Supply`, `90_CrossDomain`.

---

## 6. KPI Definition Template
KPI definitions reside per impact dimension under `/_includes/kpi_catalog/`. Use `KPI_Catalog_README.md` as entry point. Each KPI must include `strategic_ref` to `Strategic_KPIs.md`.

```
KPI Name: Gross Margin %
Purpose: Share of gross margin relative to Net Sales.
Definition: (Net Sales Amount − COGS Amount) / Net Sales Amount.
Grain & Scope: Aggregated from invoice line; valid for Actuals.
Unit/Format: % (1 decimal).
Lineage: fact_sales.Net Sales Amount, fact_sales.COGS Amount.
QA: Must be within [−100 %; 100 %]; reconcile to P&L.
```

This guarantees traceability between business intent and technical implementation.

---

## 7. Action Codes – Rationale
Action Codes standardize operational levers across all Use Cases.

| Code | Description | Typical Effect |
|------|--------------|----------------|
| **P2** | Tighten Discounts | +1 – 2 pp Gross Margin % |
| **D1** | Promo Calendar Optimization | + Forecast Accuracy |
| **M3** | Channel Mix Steering | + Revenue Stability |
| **PC2** | Renegotiate Supplier Terms | − COGS |
| **W1** | Accelerate Collections | + Cash Flow |
| **I1** | Safety Stock Optimization | − Inventory Value |

**Why use codes?**
- Common language for decision and automation triggers.  
- Enables filtering, impact tracking, and AI suggestions.  
Full list: [`/_includes/ActionCodes.md`](../_includes/ActionCodes.md).

---

## 8. Governance & Quality
**Review Workflow:**
- One **Business Reviewer** (domain expert).  
- One **Technical Reviewer** (data/model owner).

**Definition of Done:**
- All mandatory Use Case sections filled (Goal, Context, KPIs, Actions, Impact).  
- Naming + units follow conventions (`Δ`, `Δ%`, `%`).  
- Cross-references validated, glossary terms linked.  
- Changelog entry updated in `/docs/Changelog.md`.  

**Versioning:**
- Minor = text change.  
- Major = logic / KPI change.  
- Status: `Draft` → `In Review` → `Active` → `Deprecated`.

---

## 9. Continuous Improvement
- New insights from live reports feed back into the Use Case.  
- When KPIs or actions change materially, update both Use Case and Catalog.  
- Periodic housekeeping: archive duplicates, merge overlaps, keep catalog lean.

---

## 10. Authoring Checklist
- ID, title, domain, owner, impact, status, last update filled.  
- Business Goal explains “why” in ≤ 2 sentences.  
- Context defines problem + decision.  
- Key Questions map to measurable KPIs.  
- KPIs defined in catalog with purpose, formula, unit, QA.  
- Actions and expected effects listed (Action Codes).  
- Impact quantified where possible.  
- Related processes + Use Cases linked.  
- Naming / format per standard (`Δ`, `Δ%`, `%`, Amount, Qty).

---

_Last updated: 12.10.2025_  
_Linked to:_ [`Reporting_Strategy.md`](./Reporting_Strategy.md) | [`Instructions.md`](./Instructions.md) | [`KPI_Catalog`](../_includes/kpi_catalog/README.md) | [`ActionCodes.md`](../_includes/ActionCodes.md)



## 6a. Mapping Use Cases to Strategic KPIs

To ensure every analysis contributes to business outcomes, each Use Case must map to one or more Strategic KPIs.

### Step-by-Step Approach

| Step | Description | Output |
|------|--------------|---------|
| **1. Identify Strategic KPI** | Select KPI from `/_includes/Strategic_KPIs.md` that aligns with the business goal. | Strategic KPI reference |
| **2. Define Analytical Drivers** | Choose supporting KPIs (from KPI Catalog) that influence the Strategic KPI. | KPI dependency list |
| **3. Link to Use Case** | Assign existing or new Use Case(s) that quantify and explain the drivers. | Use Case reference |
| **4. Assign Action Codes** | Connect actionable levers from `/_includes/ActionCodes.md`. | Action reference |
| **5. Estimate Expected Impact** | Define expected business improvement (Δ, Δ%). | Impact estimate |

> Each Use Case must include fields:
> ```yaml
> supports_strategic_kpi: [Revenue Growth %, Gross Margin %]
> expected_impact: "+2–3 pp Revenue Growth %, +0.5 pp Gross Margin %"
> ```
> These entries are validated during the review workflow and stored in the Strategic Alignment Map.

### Example Mapping

| Strategic KPI | Supporting KPI | Use Case | Action Codes | Expected Impact |
|----------------|----------------|-----------|----------------|----------------|
| **Revenue Growth %** | Volume Growth %, Price Realization % | COM-001 Sales Performance, COM-004 Price Realization | P1, P2 | +3–5 pp Revenue Growth % |
| **Working Capital %** | DSO, DPO, Inventory Days | COR-001 Working Capital | W1, I1 | −5 days CCC |
| **Gross Margin %** | Price Discount %, COGS Amount | COM-002 Gross Margin | P2, PC2 | +0.5–1 pp GM % |
