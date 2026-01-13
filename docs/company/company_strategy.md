# Company Strategy & Strategic Alignment

Purpose:
This document defines the strategic foundation of the Analytics Framework. It establishes *why* analytics exists, *what* the organization is trying to achieve, and *how* analytical use cases are systematically derived from strategic objectives.

This document is the **primary business entry point** for executives, domain owners, and decision-makers.

Scope:

- Defines the business strategy, strategic focus areas, and success criteria.
- Defines the canonical set of Strategic KPIs.
- Defines executive-level key questions.
- Defines the strategic alignment from KPIs to use cases and actions.
- Does NOT define technical implementation details (semantic models, measures, tooling).

---

## 1. Business Context & Strategic Intent

Modern organizations do not fail due to a lack of data or dashboards.  
They fail because:

- Strategic objectives are not translated into measurable outcomes.
- KPIs exist without ownership or clear decision relevance.
- Reporting is tool-driven instead of decision-driven.
- Actions are reactive, inconsistent, or undocumented.

The Analytics Framework addresses this gap by establishing a **closed-loop system**:

> Strategy → KPIs → Use Cases → Actions → Measurable Impact

Analytics is treated as a **strategic capability**, not a reporting function.

---

## 2. Strategic Focus Areas

The company strategy is structured around a stable set of strategic focus areas.  
These focus areas define *what matters* at executive level and remain stable over time, even if individual KPIs or use cases evolve.

Typical strategic focus areas include:

- Growth
- Profitability
- Liquidity
- Efficiency
- Customer Value
- Service & Experience
- Governance & Risk
- ESG & Sustainability
- Innovation & People

Each focus area is represented through a small number of **Strategic KPIs**.

---

## 3. Strategic KPIs (Canonical Set)

Strategic KPIs represent the **highest level of measurement** in the organization.

They answer the question:
> “Are we winning or losing at what truly matters?”

Characteristics of Strategic KPIs:

- Few in number
- Stable over time
- Clearly owned
- Directly linked to strategic objectives
- Decision-relevant at executive level

The canonical definitions of Strategic KPIs are maintained in:

> **Canonical source:** `docs/company/strategic_kpis.md`

Strategic KPIs are intentionally **not overloaded** with operational detail.  
Operational and analytical depth is introduced through downstream use cases.

---

## 4. Executive Key Questions

Strategic KPIs alone are not sufficient.  
Executives think in **questions**, not metrics.

Examples:

- *Why is margin deteriorating despite stable revenue?*
- *Which customers are driving long-term value vs. short-term volume?*
- *Where is liquidity at risk in the next 90 days?*
- *Which operational bottlenecks limit growth?*

These **Key Questions**:

- Translate KPIs into decision-oriented thinking.
- Act as the bridge between strategy and analytics.
- Define the intent of analytical use cases.

The canonical set of Key Questions is maintained in:

> **Canonical source:** `docs/company/key_questions.md`

---

## 5. Strategic Alignment: KPIs → Use Cases → Actions

To avoid isolated dashboards and disconnected analytics initiatives, the framework enforces explicit strategic alignment.

### Alignment Principles

- Every analytical use case must support at least one Strategic KPI.
- Each Strategic KPI is supported by multiple analytical use cases.
- Use cases are the operationalization of strategy.
- Action Codes define how insights are translated into action.

This alignment is explicitly documented and governed through the **Strategic Alignment Map**:

> **Canonical source:** `docs/company/strategic_alignment_map.md`

The alignment ensures:

- Transparency from board-level objectives to analytical execution.
- Prioritization of analytics initiatives based on strategic impact.
- Avoidance of redundant or low-value reporting.

---

## 6. Governance & Review Cadence

Strategic alignment is not a one-time exercise.

The following governance principles apply:

- Strategic KPIs are reviewed periodically (e.g., quarterly).
- Alignment between KPIs and use cases is reviewed as part of portfolio planning.
- New use cases require explicit linkage to Strategic KPIs.
- KPIs without active use cases are challenged or deprecated.

Ownership is clearly defined:

- Strategic KPIs have executive ownership.
- Use cases have domain ownership.
- Actions have operational ownership.

Detailed governance mechanics are defined in:

> `docs/operating_model/data_governance.md`

---

## 7. Relationship to Other Framework Layers

This document defines the **WHY**.

Downstream layers operationalize it:

- **Analytics Operating Model (HOW):**  
  `docs/operating_model/`
- **Use Cases (WHAT):**  
  `usecases/`
- **Semantic Models, KPIs, Measures (WITH WHAT):**  
  `framework/` and `semantic_models/`

This separation ensures strategic stability while allowing analytical evolution.

---

## 8. What Success Looks Like

When this strategy layer is implemented correctly:

- Executives trust analytics as a decision instrument.
- KPIs are no longer debated, only interpreted.
- Analytics initiatives are prioritized by business value.
- Actions are consistent, measurable, and reviewable.
- The organization moves from reactive reporting to proactive steering.

This document is the **anchor** for all analytics activities in the organization.
