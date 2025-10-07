# Methodology & Rationale

## 1. Purpose
This document explains the principles and reasoning behind the standards used in the Analytics Use Case Library.  
It clarifies why we apply consistent methods (3–30–300, semantic modeling, naming) and how this drives quality, speed, and comparability.

---

## 2. Standardization Philosophy
**Why standardize?** To reduce ambiguity, accelerate delivery, and increase trust in insights.  
**Core principles:**
- One semantic language for all domains (shared KPI names, shared dimensions).
- Separation of concerns: business description (Markdown) vs. technical implementation (later artifacts).
- Reuse over reinvention: conformed dimensions, reusable measures, shared action codes.
- Documentation-first: every use case is understandable without the author.

**Benefits:**
- Faster onboarding, simpler reviews, fewer interpretation errors.
- Comparable metrics across teams and time.
- AI/Copilot-ready content due to consistent structure and terminology.

---

## 3. The 3–30–300 Communication Principle
Design every analytical page and story so that:
- **3 seconds (Insight):** The user understands the main outcome via 4–5 KPI cards (including deltas).
- **30 seconds (Story):** The user sees trends and rankings that explain where and when the change happened.
- **300 seconds (Detail):** The user can explore the root cause with drill tables, bridges, and detail visuals.

**Why it matters:**
- Reduces cognitive load and jump time from data to decision.
- Serves executives (3/30) and analysts (300) with one coherent structure.
- Enables a consistent information architecture across all reports.

**Visual standards:**
- 3s: KPI Cards (+Δ).  
- 30s: Line for time; horizontal bar for ranking; waterfall for bridges.  
- 300s: Table/Matrix (drill & export), scatter for correlation; avoid pie/donut (use 100%-stacked).  
- ≤ 3 slicers per page; meaningful reference lines; sparing use of color.

---

## 4. Semantic Modeling 101
**Goals:** performance, reusability, reliability.

**Rules:**
- Star schema: fact tables at a clear grain; conformed dimensions for cross-domain analyses.
- Time intelligence via role-playing date dimensions when needed.
- Prefer measures over calculated columns; use display folders by domain.
- Referential integrity ≥ 99.9 %; enforce surrogate keys on dimensions.
- RLS/OLS applied only on dimensions (e.g., organization, customer).

**Impact:**
- Predictable DAX, lower model complexity, easier testing and automation.

---

## 5. Measure & Naming Standards
**Objectives:** readability, precision, machine-interpretability.

**Conventions:**
- Percentages **always end with `%`** (e.g., `Gross Margin %`).
- Absolute variance **always starts with `Δ`** (e.g., `Δ Net Sales Amount`).  
- Percentage variance **always starts with `Δ%`** (e.g., `Δ% Net Sales`).  
- Currency metrics end with `Amount`; quantities with `Qty`; counts with `Count` / `DistinctCount`.
- Time scopes as suffixes: `YTD`, `MTD`, `QTD`, `YoY`, `MoM` (e.g., `Gross Margin % YoY`).

**Formatting:**
- Amount = currency (0–2 decimals), Qty/Count = integer, % = 1–2 decimals.

**Display folders (examples):**
- `01_Sales`, `02_Margin`, `04_Cash`, `05_Customer`, `08_Supply`, `09_Procurement`, `90_CrossDomain`.

---

## 6. KPI Definition Template
Every KPI used in a use case must be defined once in the shared catalog (`/_includes/KPI_Catalog.md`).  
Use the following structure:

```
KPI Name: Gross Margin %
Purpose: Share of gross margin relative to Net Sales.
Definition: (Net Sales Amount − COGS Amount) / Net Sales Amount.
Grain & Scope: Aggregated from invoice line; valid for Actuals.
Unit/Format: % (1 decimal).
Lineage: fact_sales.Net Sales Amount, fact_sales.COGS Amount.
QA: Must be within [−100%; 100%]; reconcile to P&L.
```

This ensures traceability for both business and technical audiences.

---

## 7. Action Codes (Levers) – Rationale
Action codes standardize how we describe operational levers across use cases.  
Examples:
- **P2** Tighten Discounts (pricing discipline)  
- **D1** Promo Calendar Optimization  
- **M3** Channel Mix Steering  
- **PC2** Renegotiate Supplier Terms  
- **W1** Accelerate Collections  
- **I1** Safety Stock Optimization

**Why use codes?**
- Consistent language for decisions and automation.
- Triggers and notifications can reference codes unambiguously.
- Easy filtering of use cases by lever categories.

A full list with descriptions lives in `/_includes/ActionCodes.md`.

---

## 8. Review, Governance, and Quality
**Review workflow:**
- One business reviewer (subject matter expert)
- One data reviewer (model/metric owner)

**Definition of Done:**
- All mandatory sections are filled (Goal, Context, Questions, KPIs, Actions, Impact).
- Naming follows conventions (Δ, Δ%, %).
- Cross-references validated; glossary terms present where needed.
- Changelog entry created and merged.

**Versioning:**
- Minor version for text refinements; major version for KPI/logic changes.
- Status tags: `Draft`, `In Review`, `Active`, `Deprecated`.

---

## 9. Continuous Improvement
- New insights from live reports are fed back into the use case.
- When actions or KPIs change materially, update the One-Pager and Changelog.
- Periodic housekeeping: archive or merge overlapping use cases, keep the catalog lean and clear.

---

## 10. Appendix: Authoring Checklist
- Title, ID, domain, owner, impact, status, and last update are set.
- Business Goal explains the “why” in one or two sentences.
- Context describes the problem and decisions supported.
- Questions are actionable and map to KPIs.
- KPIs are defined in the catalog (with purpose, formula, unit, QA).
- Actions list what to do and expected effect on KPIs.
- Expected Business Impact is quantified where possible.
- Links to related processes and use cases are added.
- Naming and units follow standards (Δ, Δ%, %, Amount, Qty).

---

Last updated: 07.10.2025
