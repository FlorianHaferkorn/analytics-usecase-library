# Legacy: Action-Ready Baseline and Blueprint (archived 2026-02)

**Status:** Legacy. These artifacts are no longer part of the active framework. They can be deleted once no external references remain.

## Contents

- **core_action_ready/** — Former `core/semantic_models/core_action_ready/`: baseline semantic model placeholder (model_definition.yaml, README). The framework no longer uses a single "core action ready" model; semantic structure is defined by **semantic_layer.md**, **UseCase_Bracket.yaml**, **data contracts**, and **domain measure dictionaries**. Showcases use domain semantic models (e.g. Aurora: Commercial.SemanticModel, Finance.SemanticModel).
- **ActionReady_SemanticModel_Blueprint.md** — Former detailed reference blueprint. The technical connection to semantic models is via **Brackets** (orchestration, KPIs, layout) and **data contracts**; this document was narrative-only and is not consumed by tooling.

## Canonical replacements

| Former | Replacement |
|--------|-------------|
| Core semantic model definition | `core/strategy_operating_model/operating_model/semantic_layer.md` (conceptual); UseCase_Bracket.yaml + core/kpi_catalog + core/data_contracts/domains (technical) |
| Action-ready blueprint | semantic_layer.md; structure is implemented via data contracts and domain models |

## Safe to delete

This archive folder may be removed when:
- No links or docs point to `internal/archive/legacy_action_ready_and_blueprint_2026-02/` for active use.
- You have confirmed SSOT and conventions point only to semantic_layer.md and Bracket-driven generation.
