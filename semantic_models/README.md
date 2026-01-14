# Semantic Models

## Purpose

Semantic Models define the **computable meaning layer** of analytics.
They translate business intent, governed KPIs, and data contracts into **stable, reusable, and decision-safe logic** that can be consumed by all use cases and tools.

Semantic Models ensure that:

- KPIs are calculated consistently.
- Business meaning is separated from data sources.
- Analytics scales without semantic drift.
- Automation and AI operate on trusted definitions.

---

## Scope

This layer defines:

- Domain-level semantic cores (“Golden Semantic Models”)
- Canonical measures and aggregations
- Explicit analytical assumptions
- Reusable semantic patterns across use cases

This layer does **not**:

- Define business strategy
- Introduce new KPIs
- Contain use-case-specific logic
- Implement tool- or report-specific behavior

---

## Golden Semantic Models

### Definition

Golden Semantic Models define the **canonical, governed meaning layer** for each business domain.

> Each domain owns exactly one Golden Semantic Core.  
> Use cases consume semantic cores — they do not redefine them.

Golden Semantic Models are:

- Domain-owned
- Semantically stable
- Tool-agnostic
- Designed for reuse and automation

They represent the **single source of computable truth** for analytics.

---

## Definition of Done (DoD)

A domain-level Golden Semantic Model is considered **done** when:

- Canonical dimensions are defined and stable (e.g., Date, Organization, Product, Customer).
- Domain KPIs are fully covered and mapped to the KPI Catalog.
- Measure assumptions are explicit (managerial vs. accounting, snapshot vs. flow).
- Grain and aggregation rules are documented and enforced.
- No use-case-specific logic exists in the semantic core.
- All measures reference stable identifiers (KPI IDs, Action Codes).

Once done, a Golden Semantic Model becomes **read-only** for use cases.

---

## Domain Scope & Ownership

### Domain Ownership

- Each domain (e.g., Growth, Profitability, Liquidity, Service) owns its semantic meaning.
- Ownership includes KPI definitions, interpretation, and valid actions.
- Ownership does **not** include tool-specific implementation.

### Scope Rules

- Each KPI belongs to exactly one domain.
- Domains may expose KPIs for cross-domain usage but never delegate ownership.
- Domain KPIs must be sufficient to cover all Core Use Cases of that domain.

---

## Cross-Domain Sharing Rules

Cross-domain analytics is enabled through **shared dimensions**, not shared KPI logic.

### Allowed

- Shared canonical dimensions (Date, Organization, Product, Customer)
- Side-by-side usage of domain KPIs in cross-domain views
- Derived comparisons at report level without redefining semantics
- Alias measures that explicitly reference the canonical KPI without redefining logic

### Not Allowed

- KPI logic spanning multiple domains
- Redefining KPIs in consuming domains
- Use-case-specific extensions inside domain semantic cores

### Alias Strategy (Cross-Domain Use)

When a KPI is needed in multiple domains (e.g., Net Sales for Revenue per FTE), use an **alias measure**:

- The canonical domain keeps the single KPI definition (`is_kpi_measure: true`, `kpi_id_ref` set).
- Consuming domains create an alias with **no KPI ownership**:
  - `is_kpi_measure: false`
  - `kpi_id_ref: ""`
  - `expression.dax` references the canonical measure (no new logic)

This preserves single ownership while enabling reuse.

> Cross-domain insights emerge from composition, not from new semantic definitions.

---

## Anti-Patterns (Explicitly Prohibited)

The following patterns are intentionally not allowed:

- Defining KPIs inside reports or use cases
- Creating ad-hoc or temporary measures for convenience
- Embedding business logic in visuals or filters
- Forking semantic logic per use case
- Using tool-specific features to bypass semantic governance

These patterns undermine trust, scalability, and AI-readiness.

---

## Relationship to Other Framework Layers

- **Framework** defines what KPIs mean and which actions are valid.
- **Data Contracts** define which data is required.
- **Semantic Models** define how meaning becomes computable.
- **Use Cases** define where and why meaning is applied.

Semantic Models are the **bridge between intent and execution**.

---

## Why This Matters (Customer Perspective)

Without Golden Semantic Models:

- KPIs drift over time.
- Each new use case increases complexity.
- Automation and AI amplify inconsistencies.

With Golden Semantic Models:

- New use cases are configuration, not rework.
- KPIs remain stable even as tools change.
- AI agents operate on trusted semantics.

---

## Outcome

When applied correctly:

- Semantic consistency scales with the organization.
- Analytics remains trustworthy under change.
- Prescriptive actions are grounded in stable meaning.
- AI and automation become safe to deploy.

Semantic Models are not an implementation detail.  
They are the **foundation of sustainable, enterprise-grade analytics**.
