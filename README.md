# ActionReady Analytics Framework

Purpose:
Actionable, governed, and reusable analytics architecture that turns strategy (WHY) into operating standards (HOW), implementation assets (WITH WHAT), and customer-grade use cases (WHAT).

Four-layer model:
```
WHY      docs/company
HOW      docs/operating_model
WITH WHAT framework/ (templates, KPI catalog, Action Codes, guides)
WHAT     usecases/ + semantic_models/ + data_contracts/ + showcases/
```

Getting started:
1) Read `docs/company/` for domains, strategic KPIs, and key questions.  
2) Apply `docs/operating_model/semantic_layer.md` and `measure_system.md` when building models.  
3) Use `framework/templates/` and `framework/kpi_catalog/` to design reports and measures.  
4) Implement or reuse core use cases in `usecases/core/` (Business/Technical Factsheets v1.2).  
5) See the end-to-end Aurora example in `showcases/aurora_group/`.

Quality & governance:
- KPI catalog and measure dictionary are the canonical sources; every measure maps to a `kpi_id`.
- Data contracts → semantic models → measures → visuals must stay consistent with the operating model.
- Action Codes drive “now-what”; every trigger references a KPI and measure.
- UX follows the 3–30–300 patterns in `framework/templates/page_templates/`.
- Validation tools live in `_internal/tools/validation/` (factsheets vs KPI, measures vs catalog, etc.).

What “good” looks like:
- OneLake-aligned data contracts with conformed dimensions (dim_date, dim_org, dim_product, dim_customer, security_user_org).
- Semantic models with single-direction relationships, governed folders, and RLS/OLS per `data_governance.md`.
- Business and Technical Factsheets that are automation-ready and AI-friendly.
- Aurora showcase proving the patterns end to end.
