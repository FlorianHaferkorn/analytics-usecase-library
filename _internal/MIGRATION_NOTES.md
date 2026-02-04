# Migration Notes (Non-breaking)

Goal: evolve the repository structure toward a product-grade separation of:
- **tool-agnostic framework** (contracts, catalogs, use cases, templates)
- **tool-specific implementations** (Fabric/Power BI adapter)
- **showcases** (examples)
- **maintainer-only internals** (`_internal/`)

Constraint: keep **Stage 1 green** during the transition.

## Strategy

1. **Introduce target folders first** (scaffolding only). Do not move existing source-of-truth folders yet.
2. Update tooling to be **path-flexible** (accept old and new roots via parameters).
3. Migrate content in **cohesive units** (e.g. use cases + maps + templates together).
4. After at least one full green CI cycle, remove the old paths.

## Target (high level)

```yaml
framework/                       # tool-agnostic product
implementations/                 # tool-specific adapters
showcases/                       # examples
_internal/                       # maintainer-only
```

## Current → Target mapping

- `docs/` → `framework/strategy_operating_model/` **done** (strategy + operating model; Golden Thread)
- `usecases/` → `framework/usecases/` **done**
- `data_contracts/` → `framework/data_contracts/` **done**
- `semantic_models/` → `framework/semantic_models/` **done**
- `powerbi-theme/` → `implementations/microsoft_fabric_powerbi/tools/theme_generator/` **done**
- `Sample_Report/` → `showcases/sample_pbip_report/` **done** (example PBIP report with PBIR files)
- `dist/` → `implementations/microsoft_fabric_powerbi/dist/` **done** (Fabric/Power BI output and checks reference this folder only)
- `framework/implementation_guides/` → `implementations/microsoft_fabric_powerbi/guide/` **done**; stub at `framework/implementation_guides/README.md` redirects
- `framework/` (current) stays; later may be split into framework submodules
- `showcases/aurora_group/` stays under `showcases/`
- `_internal/tools/` stays maintainer-only

## What must not break

- Stage 1 checks in `_internal/tools/run_stage1_checks.ps1`
- Schema validation and stable IDs
- Canonical files referenced by docs and templates

