# Operating Model Overview

## Purpose

Define how strategy is translated into governed analytics and action at scale.

## Core components

1. Golden Thread (`golden_thread_strategy_to_action.md`)
2. Semantic Layer (`semantic_layer.md`)
3. Measure System (`measure_system.md`)
4. Data Governance (`data_governance.md`)
5. Distribution Architecture (`distribution_architecture.md`)
6. UX Design System (`ux_design_system.md`)
7. Ownership and RACI (`ownership_raci_golden_thread.md`)
8. Core Constitution (`core_constitution.md`)
9. AI-first Operations (`ai_first_operations.md`)
10. Supply Chain & Security (`supply_chain_security.md`)

## Delivery principle

- Core definitions remain tool-agnostic in `core/`.
- Product implementations consume these definitions in `products/`.
- Validation and generation run via `tooling/`.

## Quality gates

- Stage 1 (CI gate): `tooling/run_stage1_checks.ps1`
- Registry audit: `tooling/ontology/registry_builder.py --strict`
- Full checks: `tooling/run_all_checks.ps1`
- Pre-commit: `tooling/git-hooks/pre-commit` (runs registry in strict mode)

## Artifact design laws

Binding design principles are codified in `data_governance.md` §7:
Separation of Concerns, SSOT, Transitive Integrity, Roles-Not-Names, Zero-Tolerance Gatekeeping.

Origin: [ActionReady Holistic Manifesto](../../../internal/vision/ACTIONREADY_HOLISTIC_MANIFESTO.md)

## Related documents

- Data layer standard: `data_layers_standard.md`
- Single source of truth: `reference/single_source_of_truth.md`
- Framework audit & trust signals: `data_governance.md` §8–§9
- Playbook: `core/implementation_guides/playbook_strategy_to_first_report.md`

---

## Sources & Grounding

This overview applies the standard **Target Operating Model (TOM)** discipline — translating
strategy into a coherent design of people, process, technology and governance — specialized
to a **data & analytics operating model**. The "Core components" and "Quality gates" sections
correspond to the people/process/technology/governance layers of a TOM, and the tool-agnostic
core / product-implementation split reflects a federated D&A operating-model design. Grounded in:

- **Data & analytics operating model design** (linking the operating model to strategy and
  quantifiable business outcomes; architecture and scope of D&A work) — Gartner, *How to
  Design a High-Impact Data and Analytics Operating Model*:
  <https://www.gartner.com/en/documents/5881411> · Gartner Data & Analytics Strategy:
  <https://www.gartner.com/en/data-analytics/topics/data-analytics-strategy>
- **Target Operating Model components** (the people / process / technology / governance
  layers a TOM is built from) — KPMG Target Operating Model (Powered Enterprise, six layers
  including Process, People, Technology, Performance Insights and Governance):
  <https://kpmg.com/xx/en/what-we-do/services/advisory/consulting/kpmg-powered-enterprise/kpmg-target-operating-model.html>
- **Data & analytics operating model in practice** (operating-model archetypes and the
  centralized/federated/decentralized trade-offs) — Deloitte, Data & Analytics Operating
  Model:
  <https://www2.deloitte.com/us/en/pages/consulting/articles/data-analytics-operating-model.html>

> This framework keeps **core definitions tool-agnostic** and pushes tool-specific work to
> product implementations — a federated operating-model choice; the governance "Quality gates"
> above are the framework's process layer (CI, registry audit, pre-commit).
