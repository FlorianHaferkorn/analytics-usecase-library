# Analytics Operating Model (HOW)

## 1. Purpose and Scope

This document defines how the Golden Thread is operated in practice.

While the Golden Thread describes the causal logic from strategy to action, the Operating Model ensures that this logic can be built, maintained, governed, and scaled over time.

The Operating Model does not introduce new analytical concepts.
It translates the Golden Thread into clear responsibilities, lifecycle rules, and quality mechanisms.

Its purpose is to ensure that:

- analytical logic remains consistent as change occurs,
- ownership and decision rights are clear,
- and the framework remains operable as complexity grows.

All elements described in this document exist to support and preserve the Golden Thread.

## 2. Operating Principles

The Operating Model follows a small set of principles that protect the integrity of the Golden Thread in daily operation.

Analytical logic is defined once and reused.
Analytical outputs are designed to support decisions and actions.
Business meaning is not reinterpreted at the point of consumption.

Changes are introduced deliberately and along the existing causal chain.
New requirements extend existing logic rather than duplicating it.

Ownership is explicit.
Every artifact has a responsible owner who governs meaning, quality, and evolution.

Separation of concerns is enforced.
This creates the structural preconditions for automation and assisted analytics.
Strategy, decision logic, semantics, and presentation are handled at their respective layers.

Governance is lightweight but binding.
Rules exist to enable speed and consistency, not to introduce overhead.

These principles ensure that analytics remains trustworthy, scalable, and operable as complexity grows.

## 3. Ownership and Roles

Clear ownership is required to preserve the integrity of the Golden Thread.

Ownership in the Operating Model is defined per artifact type, not per organizational unit.
Roles exist to govern meaning, quality, and evolution — not to execute technical tasks.

Each core artifact has an explicit owner:

- Strategy and Strategic KPIs are owned by the business.
- Use Cases and Action Codes are owned jointly by business and analytics.
- Semantic Models, Measures, and Data Contracts are owned by analytics.
- Governance rules are owned centrally to ensure consistency.

Owners are responsible for:

- defining and maintaining meaning,
- approving changes,
- and ensuring alignment with the Golden Thread.

Execution may be delegated.
Ownership remains accountable.

By separating ownership from implementation, the framework remains scalable across teams, domains, and operating models.

## 4. Artifact Lifecycle

Artifacts in the Golden Thread are created and evolved along the causal chain.

A new artifact is introduced only when it is required to express a change in meaning, decision logic, or scope.
Existing artifacts are extended or adjusted whenever possible.

Changes propagate deliberately.
A change in strategy may affect KPIs and use cases.
A change in a KPI may affect measures and reports.
Downstream artifacts adapt only when their meaning or dependencies are impacted.

Artifacts move through a controlled lifecycle from creation to review.
Explicit versioning and validation ensure that change remains intentional and traceable.

By following the causal structure of the Golden Thread, the lifecycle of artifacts remains controlled, transparent, and scalable.

**Reference documents:**

- `docs/operating_model/semantic_layer.md`
- `docs/operating_model/measure_system.md`
- `docs/operating_model/reference/ActionReady_SemanticModel_Blueprint.md`

## 5. Governance and Quality Gates

Governance exists to preserve consistency and trust in the Golden Thread.

It ensures that changes do not silently alter meaning, break dependencies, or introduce inconsistent logic.
Governance is applied where semantic stability matters, not everywhere.

Quality gates are used to validate:

- consistency with the Golden Thread,
- correctness of definitions and calculations,
- and alignment with ownership and principles.

Governance does not aim to slow down delivery.
It provides clarity on when review is required and when teams can move independently.

By focusing governance on meaning and dependencies rather than tooling or process, the framework remains reliable without becoming rigid.

**Reference document:**

- `docs/operating_model/data_governance.md`

## 6. Change and Evolution

Change is an expected condition of the analytics system.

Strategic priorities evolve, KPIs are refined, new use cases emerge, and data landscapes change.
The Operating Model ensures that such change is absorbed without breaking the Golden Thread.

Changes follow the existing causal structure.
Only artifacts whose meaning or dependencies are affected are adjusted.
Unrelated elements remain stable.

Evolution is incremental.
New requirements extend existing logic rather than replacing it.

Automation and validation support change without introducing friction or uncontrolled drift.

By anchoring change in causality and ownership, the framework allows analytics to evolve continuously while preserving consistency and trust.

**Reference document:**

- `docs/operating_model/distribution_architecture.md`

## 7. UX, Design and Interaction Standards

User experience is standardized to ensure consistent interpretation and adoption of analytics.

Because analytical logic is governed centrally, interaction and presentation must not introduce ambiguity or unnecessary cognitive load.
Users should recognize structure, intent, and decision context across reports and use cases.

UX standards ensure that:

- analytical outputs are easy to interpret,
- attention is directed toward decisions and actions,
- and interaction patterns remain consistent across domains and teams.

UX rules and templates are defined outside this document.
They operationalize these standards without redefining analytical logic.

Consistent user experience reinforces trust in analytics and supports effective decision-making at scale.

**Reference document:**

- `docs/operating_model/ux_design_system.md`

## 8. Tooling, Automation and Enablement

Tools and platforms exist to support the operation of the Golden Thread.

They do not define analytical logic, business meaning, or decision intent.
These are established by the Golden Thread and governed through the Operating Model.

Tooling is used to:

- reduce manual effort in creating and maintaining artifacts,
- enforce consistency through standardization,
- and support collaboration across teams and domains.

Automation and AI act as accelerators.
They assist in creating, validating, and evolving artifacts based on existing definitions and rules.
They do not introduce new business logic or replace ownership.

Because artifacts are explicit and structured, assisted operation becomes possible.
This enables the framework to scale without increasing operational overhead.

As a result, tooling and automation strengthen the Golden Thread by making its operation efficient, repeatable, and sustainable.

**Reference document:**

- `docs/operating_model/ai_readiness.md`

## 9. Operational Outcome

When the Operating Model is applied consistently, analytical logic remains stable as scale and complexity increase.

The model enables collaboration between business and analytics, preserves semantic consistency, and supports reliable decision-making independent of tooling choices.
