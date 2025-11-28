# ActionReady Analytics Framework

## Purpose
The **ActionReady Analytics Framework** provides a complete, platform-agnostic, enterprise-grade structure for transforming business strategy into governed analytics products.  
This repository is the **single source of truth** for:

- strategic alignment (WHY),
- operating model (HOW),
- implementation patterns (WITH WHAT),
- reusable templates & semantic standards (PATTERNS),
- and fully implemented example use cases (WHAT).

It replaces fragmented reporting with a **consistent, scalable, action-driven analytics architecture** — independent of platform, but with first-class support for Microsoft Fabric/Power BI.

---

# The Four-Layer Architecture

Below is the complete architecture in a compact, consulting-ready ASCII diagram.

```
                    ┌────────────────────────────────────────────────┐
                    │                 COMPANY LAYER (WHY)            │
                    │  - Business Strategy                           │
                    │  - Domains                                     │
                    │  - Strategic KPIs                              │
                    │  - Key Questions                               │
                    └────────────────────────────────────────────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │             OPERATING MODEL (HOW)              │
                    │  - Data Contracts                              │
                    │  - Semantic Layer Rules                        │
                    │  - Measure System                              │
                    │  - UX Standards (3-30-300)                     │
                    │  - Distribution Architecture                   │
                    │  - AI / Copilot Readiness                      │
                    │  - Governance & Operations                     │
                    └────────────────────────────────────────────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │            FRAMEWORK TOOLKIT (WITH WHAT)       │
                    │  - Templates (Page, Measure, Data Contract)    │
                    │  - Action Codes (L1/L2/L3)                     │
                    │  - KPI Catalog & Measure Dictionary            │
                    │  - Glossaries (Business & Technical)           │
                    │  - Platform Implementation Guides              │
                    └────────────────────────────────────────────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │               USE CASE LAYER (WHAT)            │
                    │  - Core / Extended / Industry Use Cases        │
                    │  - Business & Technical Factsheets             │
                    │  - Required KPIs / Action Codes                │
                    │  - Page Templates & Navigation                 │
                    │  - Semantic Model Mapping                      │
                    └────────────────────────────────────────────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────────────┐
                    │                   SHOWCASES                    │
                    │        Aurora Group (end-to-end example)       │
                    │  - Strategy → Semantics → Pages → Actions      │
                    │  - Full model & data contract implementation   │
                    │  - Demonstrates best practices in context      │
                    └────────────────────────────────────────────────┘
```

This diagram shows how strategy flows into semantics, semantics into KPIs/measures, and KPIs into governed reporting and actions.

---

# Getting Started

### 1. Start with the Business Layer
Read:
- `docs/company/business_strategy.md`
- `docs/company/domains.md`
- `docs/company/strategic_kpis.md`

### 2. Understand the Operating Model
Review:
- `docs/operating_model/semantic_layer.md`
- `docs/operating_model/measure_system.md`
- `docs/operating_model/ux_standards_3-30-300.md`
- `docs/operating_model/ai_readiness.md`

### 3. Explore the Tooling & Templates
See:
- `framework/templates/`
- `framework/kpi_catalog/`
- `framework/action_codes/`
- `framework/implementation_guides/fabric_powerbi.md`

### 4. Explore Use Cases
Check:
- `usecases/core/`
- `usecases/extended/`
- `usecases/industry/`

### 5. Explore the Showcase (Aurora Group)
A fully implemented, end-to-end example showing how everything ties together.  
→ `showcases/aurora_group/`

---

# Repository Structure (High-Level)

```
analytics-framework/
  docs/
    company/
    operating_model/

  framework/
    implementation_guides/
    templates/
    action_codes/
    kpi_catalog/
    glossary/

  semantic_models/
    core_action_ready/
    domains/

  data_contracts/
    domains/
    sources/

  usecases/
    core/
    extended/
    industry/
    templates/

  showcases/
    aurora_group/

  assets/
    branding/
    org/
    value_chain/

  _internal/
```

---

# Quality & Governance

### Measure System & KPI Consistency
Measures must follow:
- taxonomy,
- naming rules,
- foldering standards,
- documentation template,
- and correspond to a `kpi_id`.

### Use Case Traceability
Every use case must map:
- Business goal → Strategic KPIs  
- KPIs → Measures  
- Measures → Semantic Model  
- Semantic Model → Data Contracts  
- Data Contracts → Domains

### Validation (Internal)
Tools in `_internal/tools` can validate:
- KPI Catalog
- Factsheet integrity
- Generated measures
- Semantic model alignment

---

# When to Use This Framework

Use this framework when you need:
- scalable enterprise analytics,
- governed KPIs,
- consistent measure and semantic modeling,
- professional UX standards (3-30-300),
- actionability through Action Codes,
- AI-ready reporting and metadata,
- and a complete example to onboard teams (Aurora Group).

---

**Location:**  
`README.md`
