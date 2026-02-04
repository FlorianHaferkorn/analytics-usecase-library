# Implementation Tools (Fabric / Power BI)

This folder will contain **implementation-facing tooling** for Fabric/Power BI.

Principle:
- Framework governance tooling stays in `_internal/tools/` (maintainer-only).
- Implementation tooling here should be **safe to mirror into customer implementations** (or packaged) without leaking maintainer internals.

## What belongs here

- **run_fabric_checks.ps1** — runs Fabric-specific validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices in TMDL). Invoke from repo root. Scripts live under `../validation/` (check_measures_vs_kpi.ps1, check_tmdl_vs_measure_dictionary.ps1, check_dax_best_practices.ps1).
- Wrapper scripts for common workflows (generate measures, validate TMDL, validate PBIP, apply theme)
- \"Reproduce Aurora\" helpers (end-to-end local steps)
- Non-destructive utilities (format, lint, verify)

## Current sources (until we migrate)

- `_internal/tools/` (validation, generation, BPA, Power BI MCP)
- `theme_generator/` (theme generation; Power BI Theme Generator)

