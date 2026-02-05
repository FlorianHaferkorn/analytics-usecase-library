# Microsoft Fabric / Power BI Implementation (Adapter)

This folder contains the **tool-specific adapter** that implements the tool-agnostic framework artifacts (KPIs, use cases, action codes, templates) on **Microsoft Fabric + Power BI**.

## Scope

Included:
- Fabric/Power BI architecture patterns (workspaces, lakehouse, semantic model, report distribution)
- PBIP/TMDL conventions and best practices
- Deployment-as-code scaffolding (setup/teardown by code)
- Implementation tooling (validation, linting, generation, report/theme tooling)

Not included:
- Tool-agnostic framework assets (those stay in `framework/` including `framework/strategy_operating_model/`, `framework/usecases/`, `framework/data_contracts/`, `framework/semantic_models/`)
- Customer-specific provisioning details (handled via parameterization and deployment configuration)

## Current sources of truth (until we migrate content)

Implementation guide(s):
- `guide/fabric_architecture_best_practices.md` — workspace strategy, CI/CD, Git, governance (framework-fit)
- `guide/fabric_powerbi.md`
- `guide/tmdl_best_practices.md`

Tooling (maintainer/internal, may later be mirrored here):
- `_internal/tools/` (Stage 1, validation, generation, BPA, Power BI MCP)

Theme tooling:
- `tools/theme_generator/` (Theme Generator and documentation)

Aurora reference implementation:
- `showcases/aurora_group/` (PBIP semantic model + report assets)

## Repo structure and where generated TMDL goes

**Three layers:**

| Layer | Path | Role |
|-------|------|------|
| **Framework** | `framework/` | Spec only: use cases, KPI catalog, data contracts, templates. No generated output. |
| **Implementation** | `implementations/microsoft_fabric_powerbi/` | Adapter: guide, tools, validation. **dist** = output for customer rollout (per-use-case TMDL). |
| **Showcase** | `showcases/aurora_group/` | Special case to **prove the framework**: company profile, data/gold, **semantic_models/** (CoreActionReady.pbip). Use `-UseAuroraShowcase` to generate into it. |

**Two output modes:**

1. **Aurora showcase (framework proof):** `-UseAuroraShowcase` → **ONE** `_Measures.tmdl` in `showcases/aurora_group/semantic_models/.../tables/`, all measures organized by `displayFolder` (= Use-Case-ID or catalog-defined folder). This is the primary target for framework validation.

2. **dist (customer rollout / CI):** Without `-UseAuroraShowcase` → one `_Measures.tmdl` **per use case** in `dist/<UseCase>/<UseCase>.SemanticModel/...`. Used for CI validation and as starting point for customer projects.

**Summary:** Use `-UseAuroraShowcase` for the framework-proof showcase; omit it to write to dist (customer rollout or CI).

## Planned structure

```yaml
implementations/microsoft_fabric_powerbi/
  dist/                  # output for customer rollout (per-use-case TMDL); Aurora = special case to prove framework
  deployment/            # IaC + scripts (create/destroy environments)
  guide/                 # fabric_powerbi.md, tmdl_best_practices.md
  validation/            # Fabric-specific checks (measures vs KPI, TMDL, DAX)
  pbip_templates/        # canonical PBIP skeletons (dataset/report)
  tools/                 # theme_generator, run_fabric_checks, test_tmdl, etc.
```

## Next step

Start with the guide (in this implementation):
- `guide/fabric_powerbi.md`

Then use the Aurora showcase as the reference implementation baseline:
- `showcases/aurora_group/`
