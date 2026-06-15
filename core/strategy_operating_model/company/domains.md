# Business Domains & Ownership Model

## 1. Purpose

This document defines the business domain structure used by the Analytics Framework.

Domains are introduced to scale and govern the Golden Thread.
They do not define strategy, KPIs, or analytical logic.
They provide stable ownership and clear boundaries as analytical complexity grows.

Domains are business constructs, not technical layers.

## 2. Why Domains Exist

As analytics scales, organizations typically encounter recurring challenges:

- overlapping KPIs with conflicting definitions,
- unclear ownership for metrics and insights,
- slow decision-making due to cross-functional ambiguity.

Domains address these challenges by introducing responsibility-driven ownership units.
They clarify who owns meaning, prioritization, and interpretation — independent of tools, data sources, or organizational structure.

## 3. Domain Design Principles

The domain model follows a small set of binding principles.

Domains are business-driven, not data- or tool-driven.
Each domain has explicit ownership.
Domains are broader than individual use cases, but narrower than company strategy.

Every use case belongs to exactly one primary domain.
Cross-domain references are allowed; ownership is not.

Domains remain stable even as implementations, tools, or organizational structures change.

## 4. Canonical Domain Set

The framework uses a canonical domain set that covers the full decision landscape.

The exact composition may vary by organization.
Any adaptation remains explicit and governed.

Domains include:

- Commercial  
  Revenue, pricing, promotions, margin steering

- Customer Value  
  Retention, churn, lifetime value, segmentation

- Operations  
  Capacity, quality, asset performance

- Supply Chain  
  Inventory, service levels, reliability, forecasting

- Finance  
  Liquidity, costs, profitability, financial control

- Experience & Service  
  Service levels, response times, customer experience

- Governance & Risk  
  Compliance, controls, audit, risk exposure

- ESG  
  Sustainability, emissions, energy, social indicators

- Innovation & People  
  Workforce, learning, innovation capability

## 5. Domain Scope & Boundaries

Each domain defines what it owns and what it explicitly does not own.

Explicit scope boundaries are mandatory to prevent overlaps and semantic conflicts.

Example: Customer Value

In scope:

- Customer lifetime value
- Churn and retention
- Customer segmentation

Out of scope:

- Pricing logic (Commercial)
- Revenue recognition (Finance)
- Campaign execution details (Commercial / Experience)

## 6. Domain Ownership Model

Each domain has a designated Domain Owner.

The Domain Owner is accountable for:

- business definitions of domain KPIs,
- relevance and prioritization of use cases,
- interpretation logic and thresholds,
- alignment of Action Codes with business reality.

The Domain Owner is not responsible for:

- data ingestion or pipelines,
- tooling configuration,
- report development,
- visual or UX implementation.

This separation ensures accountability without technical overload.

## 7. Relationship to Use Cases

Use cases are the operational units of domains.

Rules apply consistently:

- every use case belongs to one primary domain,
- use cases may reference KPIs from other domains without transferring ownership,
- cross-domain use cases still declare a single primary domain.

The domain determines KPI relevance, action applicability, and governance responsibility.

## 8. Executive & Cross-Domain Views

Executive views do not constitute a separate domain.

They:

- aggregate KPIs across domains,
- do not redefine KPIs,
- do not introduce new ownership.

Executive views provide steering transparency while preserving domain semantics.

## 9. Relationship to Other Framework Layers

Domains connect strategy to analytical execution.

They relate to:

- Company Strategy (WHY): `core/strategy_operating_model/company/company_strategy.md`
- Golden Thread & Operating Model (HOW): `core/strategy_operating_model/operating_model/`
- Use Cases (WHAT): `usecases/`
- Semantic Models & KPIs (WITH WHAT): `core/`, `semantic_models/`

All downstream artifacts remain traceable to a primary domain.

## 10. Outcome

When domains are applied consistently:

- KPI ownership is clear and undisputed,
- cross-functional discussions become faster and factual,
- use cases scale without semantic drift,
- analytics reflects responsibility rather than org charts.

Domains provide the structural backbone for scalable, governed analytics.

---

## Sources & Grounding

The domain model in this document — business-driven, stable boundaries with explicit
ownership, broader than a use case but narrower than company strategy, with each use case
belonging to exactly one primary domain — is a business-capability decomposition grounded
in **Domain-Driven Design** and the **data mesh** notion of domain ownership. The scope/
boundary and "owns meaning, not pipelines" rules mirror DDD bounded contexts and data-mesh
domain ownership. Grounded in:

- **Domain-Driven Design** (subdomains, bounded contexts, ubiquitous language; decomposition
  by business capability rather than technical layer) — Eric Evans, *Domain-Driven Design:
  Tackling Complexity in the Heart of Software* (2003), DDD Reference (CC BY 4.0):
  <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf> ·
  DDD Resources: <https://www.domainlanguage.com/ddd/>
- **Domain analysis / business-capability decomposition** (designing around business
  capabilities, identifying subdomains and bounded contexts, aligning team ownership to
  domain boundaries) — Microsoft Azure Architecture Center:
  <https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis>
- **Data mesh — domain ownership** (domain-oriented decentralized data ownership, built on
  Evans' domain-driven design; domains own analytical data as a product) — Zhamak Dehghani,
  *Data Mesh Principles and Logical Architecture* (martinfowler.com):
  <https://martinfowler.com/articles/data-mesh-principles.html>

> This framework's domains are **business constructs for ownership and governance**, not
> technical layers: a Domain Owner owns KPI meaning, prioritization and interpretation — not
> ingestion, pipelines, tooling or report development (see §6) — consistent with DDD's
> "owns the model" and data mesh's domain-ownership principle.
