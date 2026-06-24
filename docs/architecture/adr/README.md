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
| [0001](0001-pluggable-validation-backends-and-capability-tiers.md) | Pluggable Validation Backends and Capability Tiers | Proposed — deferred 2026-06-15 (bugfix kept via #308) |
| [0002](0002-official-first-agent-integration-and-guided-workflow.md) | Official-First Agent Integration and the Guided Agent Development Workflow | Proposed |
| [0003](0003-customer-activation-and-capability-gating.md) | Customer Activation and Capability-Gating | Proposed |
| [0004](0004-industry-variant-use-case-tier-taxonomy.md) | Industry-Variant Use-Case Tier Taxonomy | Proposed |
| [0005](0005-superversion-home-and-meridian-vendoring.md) | Superversion Home & Meridian-Core Vendoring | Accepted |
| [0006](0006-superversion-target-adapter-contract.md) | Superversion Target (Stack) Adapter Contract | Accepted |
| [0007](0007-studio-generate-docks-onto-superversion-core.md) | Studio Generate Docks onto the Superversion Core | Accepted |
| [0008](0008-ai-orchestration-routing-tokens-tracking-roi-config.md) | AI Orchestration: Routing/Token/Tracking/ROI via Layered Config | Proposed |
