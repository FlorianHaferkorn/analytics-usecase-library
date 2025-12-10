# ActionReady Analytics Framework – Documentation Hub

Purpose:
Orient readers to the four-layer model (WHY, HOW, WITH WHAT, WHAT) and point to the authoritative documents for each layer.

Navigate in this order:
1) Company layer (WHY): `docs/company/`
2) Operating model (HOW): `docs/operating_model/`
3) Framework standards (WITH WHAT): `framework/` (templates, KPI catalog, Action Codes, glossaries)
4) Use cases and technical backbone (WHAT): `usecases/`, `data_contracts/`, `semantic_models/`
5) End-to-end example: `showcases/aurora_group/`

ASCII map:
```
docs/
  company/         -> strategy, domains, KPIs, key questions
  operating_model/ -> semantics, UX (3–30–300), governance, AI readiness

framework/         -> templates, Action Codes, KPI catalog, glossaries
usecases/          -> core/extended/industry factsheets (Business & Technical v1.2)
data_contracts/    -> domain + source contracts (OneLake-aligned)
semantic_models/   -> core model + domain dictionaries
showcases/         -> Aurora Group reference implementation
_internal/         -> automation, validation, archive (internal only)
```

How customers should use:
- Align on strategy and KPIs in `docs/company/`.
- Adopt semantic/UX/governance standards from `docs/operating_model/`.
- Build reports with the templates and catalogs in `framework/`.
- Implement use cases using the Business/Technical Factsheets in `usecases/`.
- Validate against the Aurora showcase to see “done” quality.

How delivery teams should use:
- Mirror this structure for client projects.
- Reuse templates; never fork KPI or measure definitions.
- Keep Action Codes and layouts consistent with the canonical files.
- Run validation tools in `_internal/tools/validation/` before delivery.
