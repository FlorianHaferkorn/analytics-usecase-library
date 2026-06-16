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
