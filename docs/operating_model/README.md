# Analytics Operating Model (HOW)

Purpose:
Define how the ActionReady Analytics Framework is designed and run end-to-end: semantics, UX, governance, operations, and AI-readiness.

Scope:
- Data governance and ownership
- Semantic layer design and measure system
- UX standards (3–30–300)
- Distribution architecture and operational SLAs
- AI/Copilot readiness (metadata, glossary, prompt patterns)
- Excludes company strategy (see `docs/company/`) and tool-specific configs (see `framework/implementation_guides/`)

Structure:
```
operating_model/
  data_governance.md               roles, policies, RACI
  semantic_layer.md                semantic design rules and patterns
  ActionReady_SemanticModel_Blueprint.md  reference blueprint (action-ready model)
  measure_system.md                naming, formatting, documentation rules
  ux_design_system_3-30-300.md     global UX/visual standards
  distribution_architecture.md     delivery patterns, navigation, apps
  operations_sla_monitoring.md     SLAs, monitoring, incident handling
  ai_readiness.md                  metadata, glossary, prompt guidance
```

Usage:
- Customers: align IT, data, and business teams on one operating model.
- Delivery teams: apply these rules before designing models, measures, and pages.
- Improvement: evolve carefully; treat this as the master standard.

Relations:
- WHY: implements company strategy and domains from `docs/company/`.
- WITH WHAT: governs templates, KPI catalog, Action Codes in `framework/`.
- WHAT: guides how `usecases/`, `data_contracts/`, and `semantic_models/` are built and run.
