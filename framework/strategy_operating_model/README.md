# ActionReady Analytics Framework EUR" Documentation Hub

Purpose:
Provide a single navigation entry point into the Action-Ready Analytics Framework.

The Golden Thread defines the end-to-end causal logic from strategy to action.
All documents referenced here either feed into this logic or operationalize specific parts of it.

Navigate in this order (following the Golden Thread):

1) Company layer (WHY): `framework/strategy_operating_model/company/`
2) Operating model (HOW): `framework/strategy_operating_model/operating_model/`
3) Framework standards (WITH WHAT): `framework/` (templates, KPI catalog, Action Codes, glossaries)
4) Use cases and technical backbone (WHAT): `framework/usecases/`, `framework/data_contracts/`, `framework/semantic_models/`
5) End-to-end example: `showcases/aurora_group/` (reference implementation, not a required blueprint)

ASCII map:

```yaml
framework/
  strategy_operating_model/
    company/         -> strategy, domains, KPIs, key questions
    operating_model/ -> semantics, UX (3EUR"30EUR"300), governance, AI readiness
  usecases/          -> core factsheets (Business & Technical v1.2); extended/industry planned
  data_contracts/    -> domain + source contracts (OneLake-aligned)
  semantic_models/   -> core model + domain dictionaries
  kpi_catalog/       -> governed KPI definitions
  action_codes/      -> Action logic and thresholds
  templates/         -> page, measure, and data contract templates
showcases/         -> Aurora Group reference implementation
_internal/         -> automation, validation, archive (internal only)
```

How customers should use:

- Start by understanding the Golden Thread to align on the causal logic before diving into individual documents `framework/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md`.
- Align on strategy and KPIs in `framework/strategy_operating_model/company/`.
- Adopt semantic/UX/governance standards from `framework/strategy_operating_model/operating_model/`.
- Build reports with the templates and catalogs in `framework/`.
- Implement use cases using the Business/Technical Factsheets in `framework/usecases/` (core now; extended/industry planned).
- Validate against the Aurora showcase to see "done" quality.

How delivery teams should use:

- Mirror this structure for client projects.
- Reuse templates; never fork KPI or measure definitions.
- Keep Action Codes and layouts consistent with the canonical files.
- Run validation tools in `_internal/tools/validation/` before delivery.

