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
- `guide/fabric_powerbi.md`
- `guide/tmdl_best_practices.md`

Tooling (maintainer/internal, may later be mirrored here):
- `_internal/tools/` (Stage 1, validation, generation, BPA, Power BI MCP)

Theme tooling:
- `tools/theme_generator/` (Theme Generator and documentation)

Aurora reference implementation:
- `showcases/aurora_group/` (PBIP semantic model + report assets)

## Planned structure

```yaml
implementations/microsoft_fabric_powerbi/
  dist/                  # default output for generated TMDL/measures (generate_tmdl_measures; used by run_all_checks)
  deployment/            # IaC + scripts (create/destroy environments)
  pbip_templates/        # canonical PBIP skeletons (dataset/report)
  tools/                 # theme_generator + implementation-facing tooling
  (validation/ planned)  # implementation-specific checks (PBIP/TMDL/report)
```

## Next step

Start with the guide (in this implementation):
- `guide/fabric_powerbi.md`

Then use the Aurora showcase as the reference implementation baseline:
- `showcases/aurora_group/`

