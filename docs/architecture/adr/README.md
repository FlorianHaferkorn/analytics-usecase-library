# Architecture Decision Records (ADRs)

This folder records significant architecture decisions: the context, the
decision, and its consequences. Each ADR is immutable once accepted —
revisit a decision by adding a new ADR that supersedes the old one.

## Convention

- **Filename:** `NNNN-kebab-case-title.md` (zero-padded, sequential).
- **Status:** one of `Proposed`, `Accepted`, `Superseded by NNNN`, `Rejected`.
- **Superseding:** never delete or rewrite an accepted ADR; add a new one and
  set the old one's status to `Superseded by NNNN`.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-pluggable-validation-backends-and-capability-tiers.md) | Pluggable Validation Backends and Capability Tiers | Accepted — salvaged via #321 (2026-06-16), CLI-wired via #373 (2026-07-08) |
| [0002](0002-official-first-agent-integration-and-guided-workflow.md) | Official-First Agent Integration and the Guided Agent Development Workflow | Proposed |
| [0003](0003-customer-activation-and-capability-gating.md) | Customer Activation and Capability-Gating | Proposed |
| [0004](0004-industry-variant-use-case-tier-taxonomy.md) | Industry-Variant Use-Case Tier Taxonomy | Proposed |
| [0005](0005-superversion-home-and-meridian-vendoring.md) | Superversion Home & Meridian-Core Vendoring | Accepted |
| [0006](0006-superversion-target-adapter-contract.md) | Superversion Target (Stack) Adapter Contract | Accepted |
| [0007](0007-studio-generate-docks-onto-superversion-core.md) | Studio Generate Docks onto the Superversion Core | Accepted |
| [0008](0008-ai-orchestration-routing-tokens-tracking-roi-config.md) | AI Orchestration: Routing/Token/Tracking/ROI via Layered Config | Accepted |
| [0009](0009-wirkungs-loop-action-kpi-attribution.md) | Wirkungs-Loop: Action → KPI-Snapshot-Delta → Attribution (Discovery I-8) | Accepted |
| [0010](0010-kpi-calculation-dsl-and-dax-synthesis.md) | Governed KPI Calculation DSL + Deterministic DAX Synthesis (I-10.0) | Accepted |
| [0011](0011-kpi-calculation-dsl-grammar-extension.md) | KPI Calculation DSL Grammar Extension (13-KPI Closure) | Accepted |
| [0012](0012-kpi-calculation-dsl-sql-synthesis.md) | Governed KPI Calculation DSL → Databricks SQL Synthesis | Accepted |
| [0013](0013-kpi-calculation-dsl-remaining-11-use-cases.md) | KPI Calculation DSL: Remaining 11 Use Cases (Full-Catalog Closure) | Accepted |
| [0014](0014-org-layer-over-local-first.md) | Org-Schicht über lokal-first (Discovery, I-9.1) | Proposed |
| [0015](0015-onelake-ai-era-blueprint-alignment-and-architecture-blueprint-layer.md) | OneLake AI-Era Blueprint Alignment & a Stack-Agnostic Architecture-Blueprint Layer | Accepted (2026-07-15) |
| [0016](0016-authn-authz-stack-for-the-studios.md) | AuthN/AuthZ Stack for the Studios (Descope Prior-Art → EU-OSS Options) | Proposed |
