# Business Domains & Ownership Model

Purpose:
This document defines the **business domain structure** used by the Analytics Framework.
Domains are introduced to scale and govern the Golden Thread.
They do not define strategy, KPIs, or use cases, but provide ownership and boundaries as complexity grows.

Domains are **business constructs**, not technical layers.

---

## 1. Why Domains Exist

As analytics scales, organizations typically encounter:

- overlapping KPIs with conflicting definitions,
- unclear ownership for metrics and insights,
- slow decision-making due to cross-functional ambiguity.

Domains address this by introducing **stable, responsibility-driven ownership units** for analytics.
They create clarity on *who owns what*—independent of tools, data sources, or org charts.

---

## 2. Domain Design Principles

The domain model follows these non-negotiable principles:

- Domains are **business-driven**, not data- or tool-driven.
- Each domain has **explicit ownership**.
- Domains are **broader than use cases**, but **narrower than company strategy**.
- Every use case belongs to **exactly one primary domain**.
- Cross-domain references are allowed, ownership is not.
- Domains remain stable even if implementations change.

---

## 3. Canonical Domain Set

The framework uses a canonical domain set covering the full decision landscape:

- **Commercial**  
  Revenue, pricing, promotions, margin steering

- **Customer Value**  
  Retention, churn, lifetime value, segmentation

- **Operations**  
  Capacity, quality, asset performance

- **Supply Chain**  
  Inventory, service levels, reliability, forecasting

- **Finance**  
  Liquidity, costs, profitability, financial control

- **Experience & Service**  
  Service levels, response times, customer experience

- **Governance & Risk**  
  Compliance, controls, audit, risk exposure

- **ESG**  
  Sustainability, emissions, energy, social indicators

- **Innovation & People**  
  Workforce, learning, innovation capability

The exact set may be adapted, but changes must remain **explicit and governed**.

---

## 4. Domain Scope & Boundaries

Each domain defines **what it owns** and **what it explicitly does not own**.

Example:

**Customer Value**

- In scope:
  - Customer lifetime value
  - Churn and retention
  - Customer segmentation
- Out of scope:
  - Pricing logic (Commercial)
  - Revenue recognition (Finance)
  - Campaign execution details (Commercial / Experience)

Explicit boundaries are mandatory to avoid overlaps and KPI conflicts.

---

## 5. Domain Ownership Model

Each domain has a **Domain Owner**.

The Domain Owner is responsible for:

- Business definitions of domain KPIs
- Relevance and prioritization of use cases
- Interpretation logic and thresholds
- Alignment of Action Codes to business reality

The Domain Owner is **not** responsible for:

- Data ingestion or pipelines
- Tool configuration
- Report development
- Visual or UX implementation

This separation ensures accountability without technical overload.

---

## 6. Relationship to Use Cases

Use cases are the **operational units** of domains.

Rules:

- Every use case belongs to one primary domain.
- Use cases may reference KPIs from other domains, ownership remains unchanged.
- Cross-domain use cases still declare a single primary domain.

The domain determines:

- KPI relevance
- Action applicability
- Governance responsibility

---

## 7. Executive & Cross-Domain Views

Executive use cases are **not a separate domain**.

They:

- Aggregate KPIs across domains
- Do not redefine KPIs
- Do not introduce new ownership

Executive views provide steering transparency, not new semantics.

---

## 8. Relationship to Other Framework Layers

Domains connect strategy to execution:

- **Company Strategy (WHY):**  
  `docs/company/company_strategy.md`
- **Analytics Operating Model (HOW):**  
  `docs/operating_model/`
- **Use Cases (WHAT):**  
  `usecases/`
- **Semantic Models & KPIs (WITH WHAT):**  
  `framework/` and `semantic_models/`

All downstream artifacts must be traceable back to a domain.

---

## 9. What Success Looks Like

When domains are applied correctly:

- KPI ownership is undisputed.
- Cross-functional discussions are faster and factual.
- Use cases scale without semantic drift.
- Reporting reflects responsibility, not org charts.

Domains are the **structural backbone** of scalable analytics.
