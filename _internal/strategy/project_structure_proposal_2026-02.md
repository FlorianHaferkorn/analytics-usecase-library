# Project Structure Proposal (2026-02)

Purpose: propose a repo structure that scales across multiple products while
preserving the Strategy-to-Action golden thread and governance model.

Status: proposal only. No moves executed.

---

## 1) Current pain points (observed)

- Product boundaries are unclear (framework, implementation, tools, deployment,
  showcase content are interleaved across top-level folders).
- Platform tooling is mixed into product folders in inconsistent ways
  (generation tools live in _internal, but some generators live under
  implementations).
- Generated artifacts (TMDL, PBIP, dist) are mixed with source assets, which
  blurs ownership and makes lifecycle rules unclear.
- Entry points for different audiences are scattered (execs vs implementers vs
  maintainers).

These issues slow onboarding and make the repo harder to scale as additional
products and platforms are added.

---

## 2) Big picture we are aiming for

Build a productized "ActionReady Analytics Platform" with clear layers:

1) **Core Framework (tool-agnostic)**  
   Strategy, KPIs, use cases, action codes, semantic model definitions,
   data contracts, templates.

2) **Platform Products (tool-specific)**  
   Each platform gets a product folder that contains implementation guides,
   deployment templates, platform tooling, and generated outputs.

3) **Shared Tooling**  
   Cross-platform validation, generation, and schema governance.

4) **Showcases / Reference Implementations**  
   End-to-end examples demonstrating the framework in action.

5) **Internal Governance**  
   CI, schemas, evaluations, archived material. Maintainer-only.

This aligns with the "Strategy -> KPIs -> Use Cases -> Action Codes -> Templates
-> Semantic Models -> Implementation" golden thread and makes productization
explicit.

---

## 3) Design principles

- **Separation of concerns:** core framework is independent of platform.
- **Stable public API:** core definitions are a contract; products depend on them.
- **Generated vs source separation:** dist artifacts never mixed with source.
- **Single entry per audience:** clear starting points for execs, implementers,
  and maintainers.
- **Minimal cross-dependency:** products consume core; not the other way around.

---

## 4) Proposed top-level structure (target state)

```yaml
core/                       # Tool-agnostic framework (SSOT)
  strategy_operating_model/
  usecases/
  kpi_catalog/
  action_codes/
  semantic_models/
  data_contracts/
  templates/
  glossary/

products/                   # Platform-specific products
  fabric_powerbi/
    docs/                   # Implementation guide and product docs
    tooling/                # Platform-specific generators/checks
    deployment/             # Pipelines, infra, release tooling
    templates/              # Platform templates (PBIP, themes, layouts)
    dist/                   # Generated artifacts (TMDL, PBIP, etc.)
    tests/

tooling/                    # Cross-platform tooling
  validation/               # Stage 1 + schemas
  generation/               # KPI -> measures, scaffolding, etc.
  ai/                       # Schemas and AI contracts
  cli/                      # Optional unified entrypoints

showcases/                  # Reference implementations
  aurora_group/
  ...

docs/                       # Global navigation and product index
  README.md                 # Single entry point for all audiences
  architecture/             # Big picture, roadmaps, ADRs
  product_index.md

internal/                   # Maintainers only
  ci/
  strategy/
  archive/
```

Notes:
- `core/` is a rename of the existing `framework/` folder.
- `products/` is a rename of `implementations/` and must be consistent per
  product. Each product has the same internal layout.
- `tooling/` exposes shared tools currently under `_internal/tools/` for
  consumption, while `internal/` holds maintainer-only assets.

---

## 5) Product folder contract (per product)

Each product folder must include:

- `docs/README.md` with scope, prerequisites, and entry points.
- `tooling/` for platform-specific scripts and checks.
- `deployment/` for CI/CD templates and infra assets.
- `dist/` for generated artifacts only (never hand-edited).
- `templates/` for product templates (themes, layouts, scaffolds).

This makes each product portable and easier to onboard.

---

## 6) Mapping from current to target

```text
framework/                                   -> core/
implementations/microsoft_fabric_powerbi/    -> products/fabric_powerbi/
_internal/tools/                             -> tooling/
_internal/ai/                                -> tooling/ai/
_internal/ci/                                -> internal/ci/
_internal/strategy/                          -> internal/strategy/
_internal/archive/                           -> internal/archive/
showcases/                                   -> showcases/ (unchanged)
```

Compatibility: keep shim folders or stub README links during migration to avoid
breaking scripts and documentation.

---

## 7) Migration plan (phased, low risk)

Phase 0 (now):
- Approve target structure and publish this proposal.
- Add a single "docs/README.md" as the public entry point (links to core,
  products, showcases).

Phase 1 (safe moves):
- Introduce new top-level folders (core, products, tooling, internal, docs).
- Copy or move content while keeping old paths as read-only shims.
- Update scripts and docs to reference new paths.

Phase 2 (cleanup):
- Remove legacy shims once all scripts and CI are updated.
- Enforce structure in CI (check for new content in legacy paths).

---

## 8) Non-goals

- No changes to schemas, IDs, or governance rules in this proposal.
- No redefinition of KPI or action logic.
- No platform-specific design changes; only structural clarity.

---

## 9) Recommendation

Adopt the proposed structure with a phased migration. It keeps the golden
thread intact, cleanly separates products, and makes the big picture explicit
for all audiences.

Location: _internal/strategy/project_structure_proposal_2026-02.md
