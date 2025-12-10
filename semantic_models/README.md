# Semantic Models

Purpose:
Turn data contracts into governed, AI-ready analytical structures with consistent logic, relationships, and measures.

Scope:
- Core ActionReady semantic model
- Domain-level measure dictionaries
- Modeling rules, hierarchies, and metadata required for governance and Copilot-readiness
- Excludes tool-specific deployment scripts and customer-specific variants

Structure:
```
semantic_models/
  core_action_ready/
    model_definition.yaml
    measures/
  domains/
    commercial/
    finance/
    supply_chain/
    operations/
    experience/
    executive/
```

Usage:
- Customers: see how raw data becomes governed KPIs and measures.
- Delivery teams: reuse model patterns, relationships, and measure naming; align with `docs/operating_model/semantic_layer.md`.
- Evolution: add domains and measures via governed dictionaries; keep conformed dimensions intact.

Relations:
- WHY: domains come from `docs/company/domains.md`.
- HOW: modeling rules from `docs/operating_model/semantic_layer.md` and `measure_system.md`.
- WITH WHAT: measures and Action Codes rely on semantic consistency.
- WHAT: use cases and visuals consume these models.
