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
