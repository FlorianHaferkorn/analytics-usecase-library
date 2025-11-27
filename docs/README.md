# docs

Repository purpose: Provide a customer-ready library of analytics assets structured by strategy (WHY), operating model (HOW), implementation guides (WITH WHAT), and repeatable patterns (TEMPLATES).

4-layer model:
- WHY (Company Layer): Strategy, domains, strategic KPIs, key questions.
- HOW (Operating Model): Governance, semantic layer, measure system, UX standards, distribution, SLAs, AI readiness.
- WITH WHAT (Implementation Guides): Platform-specific guides and accelerators.
- PATTERNS (Templates/Library): Templates for pages, measures, data contracts; reusable assets and catalogs.

ASCII map:
```
Layer 1  WHY           -> docs/company/
Layer 2  HOW           -> docs/operating_model/
Layer 3  WITH WHAT     -> framework/ (implementation_guides, kpi_catalog, action_codes, glossary)
Layer 4  PATTERNS      -> framework/templates/ and usecases/ pattern usage
Semantic Models        -> semantic_models/ (consumes Layers 2-4)
Use Cases              -> usecases/ (driven by Layers 1-2, uses 3-4)
Assets                 -> assets/ (branding/org/value-chain support)
Archive                -> archive/ (legacy/drafts)
```

Navigation:
- Company overview: `docs/company/`
- Operating model key docs: `docs/operating_model/`
- Semantic layer blueprint: `docs/operating_model/semantic_layer.md`
- Reporting strategy / business playbook: `docs/operating_model/distribution_architecture.md` and `docs/company/business_strategy.md`
- Aurora synthetic showcase (contracts + model): `data_contracts/sources/synthetic/` and `semantic_models/core_action_ready/`
