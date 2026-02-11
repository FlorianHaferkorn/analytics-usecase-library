# Single Source of Truth (SSOT)

Purpose:
This document defines which artifacts are canonical ("single source of truth") for each concept in the framework. It prevents duplication, drift, and conflicting definitions across folders.

Scope:

- Defines the authoritative location for strategy, KPIs, measures, use cases, action codes, data contracts, templates, and tooling.
- Defines how to reference non-canonical artifacts (link-back pattern).
- Does NOT define business content itself (that stays in the referenced artifacts).
- Does NOT replace validation tooling; it complements it.

---

## Rules (non-negotiable)

1. One concept ->' one canonical file or folder.
2. If a concept appears elsewhere, it must be a **link-back** or **derived view** (explicitly marked).
3. No canonical definition may exist in more than one place.
4. Every use case must be traceable end-to-end:
   Strategy KPI ->' Use Case ->' required_kpi_ids ->' KPI Catalog ->' Measure Dictionary ->' Data Contract ->' Semantic Model blueprint.
5. If the canonical source changes, derived views must be updated in the same PR.

Use Cases contain only references to KPIs: required_kpi_ids (IDs; in factsheets represented as required_kpis[].id) and kpi_catalog_id (file-based reference); no KPI semantics (definitions, lineage, targets, units) belong in use case artifacts.

---

## Canonical sources

| Concept | Canonical source | Derived/secondary views | Notes |
|---|---|---|---|
| Repository entry point (customer) | `README.md` | `framework/strategy_operating_model/README.md` | Root README is customer-facing "start here". |
| Docs hub / navigation | `framework/strategy_operating_model/README.md` | — | Defines the documentation map. |
| Business Strategy | `framework/strategy_operating_model/company/company_strategy.md` | Showcase variants under `showcases/*` | Strategy is framework-level; showcase is example only. |
| Domains overview (scope & boundaries) | `framework/strategy_operating_model/company/domains.md` | Domain READMEs under `framework/semantic_models/domains/*/README.md` | Domain READMEs must not contradict domain scope. |
| Strategic KPIs | `framework/strategy_operating_model/company/company_strategy.md#5-strategic-kpis` | KPI catalogs (detail), XD-003 (aggregation) | Strategic KPIs define "what matters"; catalogs define "how measured". |
| Strategic alignment map (KPI ->' Use Cases) | `framework/strategy_operating_model/company/company_strategy.md#7-strategic-alignment-inputs-to-the-golden-thread` | framework/usecases/UseCase_Inventory.md | Alignment map is the strategy linkage; Inventory is operational master list. |
| Key business questions | `framework/strategy_operating_model/company/company_strategy.md#6-executive-key-questions` | Use case Business Factsheets | Use cases operationalize key questions. |
| Reporting design principles | `framework/strategy_operating_model/company/reporting_principles.md` | `framework/strategy_operating_model/operating_model/ux_design_system.md` | Company principles set constraints; UX system operationalizes them. |
| Analytics Operating Model overview | `framework/strategy_operating_model/operating_model/README.md` | — | Index for "HOW". |
| Data governance (ownership & change) | `framework/strategy_operating_model/operating_model/data_governance.md` | Use case frontmatter owner fields | Governance defines roles + decisions; use cases reference owners. |
| Semantic layer blueprint (conceptual) | `framework/strategy_operating_model/operating_model/semantic_layer.md` | `framework/strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md` | semantic_layer.md is the entry; blueprint is the detailed reference. |
| Action-ready semantic model blueprint | `framework/strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md` | `framework/semantic_models/core_action_ready/*` | Blueprint defines the "contract"; semantic_models implements patterns. |
| Measure system (conventions) | `framework/strategy_operating_model/operating_model/measure_system.md` | `framework/templates/measure_templates/*` | measure_system.md defines naming/taxonomy; templates provide reusable scaffolds. |
| UX standards & layouts | `framework/strategy_operating_model/operating_model/ux_design_system.md` | `framework/templates/page_templates/*` | UX system is principles; page templates are patterns. |
| Distribution architecture | `framework/strategy_operating_model/operating_model/distribution_architecture.md` | `implementations/microsoft_fabric_powerbi/guide/*` | Tool-specific guides implement distribution patterns. |
| AI readiness | `framework/strategy_operating_model/operating_model/ai_readiness.md` | `_internal/ai/*.schema.json` | ai_readiness describes approach; schemas enforce structure. |
| Use case master list | `framework/usecases/UseCase_Inventory.md` | Strategy alignment map | Inventory is operational truth (status, domain, owners, etc.). |
| Use case templates | `framework/usecases/templates/*` | — | Factsheets must follow these templates. |
| Use case canonical docs | `framework/usecases/core/*/(Business_Factsheet.md, Technical_Factsheet.md)` | — | Business/Technical are the canonical per-use-case docs. |
| KPI catalog schema | `framework/templates/KPI_Catalog_templates/KPI_Catalog_SCHEMA.md` | `_internal/ai/measure_inventory.schema.json` | Schema governs catalog authoring; AI schema supports validation/agents. |
| KPI catalog (SSOT) | `framework/kpi_catalog/KPI_Catalog.md` | `framework/kpi_catalog/README.md` | Single authoritative catalog; README is navigational only. |
| Domain KPI overview (executive lens) | `framework/usecases/core/XD-003_Executive_KPI_Overview/Business_Factsheet.md` | XD-003 | Must be explicitly "derived view", not redefining KPIs. |
| Domain measure dictionary schema | `framework/semantic_models/domains/Domain_Measure_Dictionary_Schema.md` | `framework/semantic_models/domains/Measure_Dictionary_*.md` | Schema defines structure; domain dictionaries contain implementation-ready detail. |
| Domain measure dictionaries (implementation-ready) | `framework/semantic_models/domains/Measure_Dictionary_*.md` | — | This is the canonical "how to implement measures" reference per domain. |
| Core semantic model definition (baseline) | `framework/semantic_models/core_action_ready/model_definition.yaml` | `framework/strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md` | YAML is the canonical short definition; blueprint is the detailed narrative. |
| Domain semantic model READMEs | `framework/semantic_models/domains/*/README.md` | — | Must reference the blueprint + relevant measure dictionary + data contracts. |
| Action codes (portfolio) | `framework/action_codes/README.md` | — | Single authoritative list of action codes and definitions. |
| Action code usage guidance | `framework/action_codes/README.md` | — | Guidance only; must not redefine action codes. |
| Use case ->' action code mapping | `framework/usecases/UseCase_ActionCode_Map.yaml` | — | Mapping is canonical for assignments. |
| Use case ->' action code rationale | `framework/usecases/UseCase_ActionCode_Rationale.yaml` | — | Canonical rationale for "why this action code fits this use case". |
| Page template library | `framework/templates/page_templates/*` | `framework/usecases/*` layout sections | Templates define reusable patterns; use cases reference them. |
| Visual whitelist | `framework/templates/page_templates/Visual_Whitelist.md` | — | Canonical set of allowed visuals for consistent UX. |
| Data contract templates | `framework/templates/data_contract_templates/*` | — | Scaffold only; contracts live under framework/data_contracts/domains. |
| Domain data contracts | `framework/data_contracts/domains/*.yaml` | `framework/data_contracts/sources/*.yaml` | Domain contracts define semantic requirements; sources define raw system contracts. |
| Source data contracts | `framework/data_contracts/sources/*.yaml` | — | Defines system/source-specific schemas and mapping hints. |
| Synthetic data scope & generator config | `framework/data_contracts/sources/synthetic/*` | — | Used for demo/acceleration; must align with domain contracts. |
| Internal tooling (validation/generation) | `_internal/tools/*` | — | Canonical scripts for checks & generators. |
| Internal AI schemas | `_internal/ai/*.schema.json` | — | Canonical machine-readable structure definitions for agents/validators. |
| Best-practice rules (BPA/linters) | `_internal/tools/linters/*` and/or `schemas/best_practices/*` | — | Canonical location must be referenced from tooling + docs. |
| Showcase artifacts (Aurora Group etc.) | `showcases/*` | none | Showcase is never canonical for framework concepts; it is an example implementation. |

---

## Link-back pattern (required for derived views)

When a non-canonical file mentions a canonical concept, it must include a short link-back block near the top:

Example:

> Canonical definition: `../path/to/canonical_file.md`  
> Note: This document is a derived view / example and must not redefine the canonical concept.

Use relative links where possible.

---

## Anti-patterns (do not do)

- Duplicating KPI definitions in multiple files.
- Defining new KPI IDs only inside a use case factsheet.
- Putting "real definitions" into README files (READMEs are navigation + intent, not authoritative definitions).
- Allowing action code definitions to drift between portfolio and use case narratives.
- Creating measures that are not traceable to KPI IDs (unless explicitly tagged as supporting measures, documented in the domain measure dictionary).

---

## Maintenance

- Update this SSOT document when:
  - A new canonical artifact is introduced,
  - A folder is renamed/moved,
  - Validation tooling starts using a different canonical reference.
- Review SSOT in every release candidate / customer-ready milestone.


