# Company Strategy & Strategic Alignment

## 1. Purpose

This document defines the strategic inputs to the Action-Ready Analytics Framework.

It establishes why analytics exists, what the organization is trying to achieve, and which outcomes matter at executive level.
It does not define analytical logic or implementation.

The end-to-end causal logic from strategy to action is defined in:
`docs/operating_model/golden_thread_strategy_to_action.md`

This document is the primary business entry point for executives, domain owners, and decision-makers.

## 2. Scope

This document:

- defines strategic objectives and focus areas,
- defines the canonical set of Strategic KPIs,
- defines executive-level key questions,
- and provides the strategic inputs required for analytical use cases.

This document does not define:

- semantic models,
- measures,
- tooling,
- or operational analytics design.

## 3. Business Context & Strategic Intent

Organizations rarely fail due to missing data or dashboards.
They fail because strategic intent is not translated into measurable, actionable decision logic.

Common failure patterns include:

- objectives without measurable outcomes,
- KPIs without ownership or decision relevance,
- analytics driven by tools instead of decisions,
- and actions that are inconsistent or undocumented.

The Analytics Framework treats analytics as a strategic capability.
Its purpose is to translate strategic intent into measurable outcomes and decision-oriented analytics.

## 4. Strategic Focus Areas

Company strategy is structured around a small set of strategic focus areas.

These focus areas define what matters at executive level and remain stable over time, even as individual KPIs or use cases evolve.

Typical focus areas include:

- Growth
- Profitability
- Liquidity
- Efficiency
- Customer Value
- Service & Experience
- Governance & Risk
- ESG & Sustainability
- Innovation & People

Each focus area is represented through a limited number of Strategic KPIs.

## 5. Strategic KPIs

Strategic KPIs represent the highest level of measurement in the organization.

They answer the question:
“Are we succeeding at what truly matters?”

Strategic KPIs are:

- few in number,
- stable over time,
- clearly owned,
- and directly linked to strategic objectives.

Strategic KPIs intentionally avoid operational detail.
Analytical depth is introduced through downstream use cases.

Canonical definitions are maintained in:
`docs/company/strategic_kpis.md`

## 6. Executive Key Questions

Executives think in questions, not metrics.

Key Questions translate Strategic KPIs into decision-oriented thinking.
They define the intent of analytical use cases and guide analytical depth.

Examples include:

- Why is margin deteriorating despite stable revenue?
- Which customers drive long-term value?
- Where is liquidity at risk in the near term?
- Which operational constraints limit growth?

The canonical set of Key Questions is maintained in:
`docs/company/key_questions.md`

## 7. Strategic Alignment: Inputs to the Golden Thread

To avoid isolated dashboards and disconnected analytics initiatives, strategic alignment is explicit.

Strategic KPIs and Key Questions provide the inputs required by the Golden Thread.
They determine which use cases are relevant and which actions are worth pursuing.

Alignment principles:

- Every use case supports at least one Strategic KPI.
- Strategic KPIs are supported by multiple use cases.
- Actions are derived from use cases, not from metrics alone.

Alignment is documented through the Strategic Alignment Map:
`docs/company/strategic_alignment_map.md`

## 8. Governance & Review Cadence

Strategic alignment is reviewed continuously.

- Strategic KPIs are reviewed periodically.
- Use case portfolios are reviewed for strategic relevance.
- KPIs without active use cases are challenged or deprecated.

Ownership is explicit:

- Strategic KPIs are owned at executive level.
- Use cases are owned by domains.
- Actions are owned operationally.

Governance mechanics are defined in:
`docs/operating_model/data_governance.md`

## 9. Relationship to Other Framework Layers

This document defines the WHY.

Downstream layers operationalize it:

- Golden Thread (causal logic): `docs/operating_model/golden_thread_strategy_to_action.md`
- Operating Model (HOW): `docs/operating_model/`
- Use Cases (WHAT): `usecases/`
- Semantic Models & Measures (WITH WHAT): `framework/`, `semantic_models/`

This separation ensures strategic stability while enabling analytical evolution.

## 10. Outcome

When applied consistently, this strategy layer ensures that:

- analytics initiatives are prioritized by business value,
- KPIs are trusted and undisputed,
- and actions are aligned with strategic intent.

This document anchors analytics in business strategy without constraining analytical evolution.
