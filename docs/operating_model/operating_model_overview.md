# Analytics Operating Model (HOW)

Purpose:
This document defines **how analytics is organized, governed, built, and operated** across the organization.
It is the **single entry point** for understanding the Analytics Operating Model and replaces the need to read multiple standalone documents.

Scope:
- Defines roles, responsibilities, and decision rights.
- Defines how strategy is operationalized through semantic models and measures.
- Defines governance, quality, and lifecycle management.
- Defines how analytics is distributed, consumed, and scaled.
- Does NOT define company strategy or individual use case content.

---

## 1. Operating Model Principles

The Analytics Operating Model is built on five principles:

1. **Strategy-driven**  
   All analytics artifacts must trace back to company strategy and domains.

2. **Domain-owned**  
   Business domains own meaning, priorities, and actions—not tools.

3. **Semantically stable**  
   KPIs and measures are governed through a shared semantic layer.

4. **Action-oriented**  
   Insights must enable or trigger concrete actions.

5. **Automation-ready**  
   Standards, metadata, and validation enable scalable delivery.

---

## 2. Roles & Responsibilities

The operating model separates **business accountability** from **technical execution**.

### Business Roles
- **Domain Owner**
  - Owns KPI definitions and interpretation
  - Prioritizes use cases
  - Validates business relevance

- **Use Case Owner**
  - Defines analytical questions
  - Validates outcomes and actions
  - Accepts delivered analytics

### Analytics & Platform Roles
- **Analytics Architect**
  - Designs semantic models and measure systems
  - Enforces standards and patterns

- **Analytics Engineer**
  - Implements data models and measures
  - Ensures performance and quality

- **Platform Owner**
  - Owns infrastructure, access, and operations

Governance is enforced through clear ownership—not committees.

---

## 3. Semantic Layer & Measure System

The semantic layer is the **single source of truth** for analytics.

It ensures:
- Consistent KPI definitions
- Reusable measures
- Clear aggregation and grain
- Separation of business meaning from data sources

### Core Components
- Action-ready semantic model blueprint
- Domain-level semantic models
- Canonical KPI catalog
- Measure dictionaries and templates

**Reference documents:**
- `docs/operating_model/semantic_layer.md`
- `docs/operating_model/measure_system.md`
- `docs/operating_model/ActionReady_SemanticModel_Blueprint.md`

---

## 4. Data Governance & Quality

Governance focuses on **control without friction**.

Key elements:
- Canonical KPI ownership
- Explicit data contracts
- Validation and quality checks
- Change transparency and traceability

Governance is:
- Domain-driven
- Enforced via standards and tooling
- Automated where possible

**Reference document:**
- `docs/operating_model/data_governance.md`

---

## 5. Distribution & Consumption

Analytics is delivered through **role-specific, decision-oriented views**.

Distribution principles:
- Separation of strategic, tactical, and operational views
- Progressive disclosure (3–30–300)
- Clear ownership of reports and audiences
- Controlled access and sharing

Distribution architecture is:
- Tool-agnostic by design
- Optimized for scalability and governance

**Reference document:**
- `docs/operating_model/distribution_architecture.md`

---

## 6. UX, Design & Interaction Standards

User experience is standardized to reduce cognitive load and increase adoption.

Principles:
- Consistent interaction patterns
- Limited visual complexity
- Clear hierarchy and focus
- Action-oriented layouts

Concrete UX rules and templates are defined outside this document.

**Reference document:**
- `docs/operating_model/ux_design_system.md`

---

## 7. AI & Automation Readiness

The operating model is designed to support:
- Automation of repetitive tasks
- AI-assisted analysis and validation
- Metadata-driven generation and checks

This is enabled by:
- Structured factsheets
- Machine-readable contracts
- Canonical identifiers
- Explicit lineage

**Reference document:**
- `docs/operating_model/ai_readiness.md`

---

## 8. Lifecycle & Change Management

Analytics artifacts follow a clear lifecycle:
- Design → Build → Validate → Deploy → Review

Changes are managed through:
- Versioned artifacts
- Impact-aware updates
- Explicit ownership
- Automated validation

This ensures stability without slowing innovation.

---

## 9. Relationship to Other Framework Layers

This document defines the **HOW**.

It operationalizes:
- **Company Strategy (WHY):**  
  `docs/company/company_strategy.md`

It enables:
- **Use Cases (WHAT):**  
  `usecases/`

It is implemented through:
- **Framework & Semantic Models (WITH WHAT):**  
  `framework/`, `semantic_models/`

---

## 10. What Success Looks Like

When the Operating Model is applied correctly:
- Analytics delivery scales without chaos.
- KPIs are trusted and undisputed.
- Business and analytics collaborate efficiently.
- Actions are consistent and measurable.
- Tool changes do not break semantics.

This document is the **anchor** for sustainable, enterprise-grade analytics operations.
