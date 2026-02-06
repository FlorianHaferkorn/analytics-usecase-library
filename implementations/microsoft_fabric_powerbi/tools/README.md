# Implementation Tools (Fabric / Power BI)

This folder will contain **implementation-facing tooling** for Fabric/Power BI.

Principle:
- Framework governance tooling stays in `_internal/tools/` (maintainer-only).
- Implementation tooling here should be **safe to mirror into customer implementations** (or packaged) without leaking maintainer internals.

## What belongs here

- **run_fabric_checks.ps1** — runs Fabric-specific validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices in TMDL). Invoke from repo root. Scripts live under `../validation/` (check_measures_vs_kpi.ps1, check_tmdl_vs_measure_dictionary.ps1, check_dax_best_practices.ps1).
- **test_tmdl.ps1** — single-file TMDL sanity check (file exists, UTF-8 no BOM, table keyword, measures, formatString/displayFolder). Used by powerbi_mcp orchestration; see **TMDL_Testing_Guide.md** for the full 4-level validation workflow.
- **apply_report_theme** — Copy a custom theme into a PBIP report and wire base + custom theme in `definition/report.json`. Use `apply_report_theme.py` or `apply_report_theme.ps1`. Example (from repo root): `py implementations/microsoft_fabric_powerbi/tools/apply_report_theme.py path/to/Report --theme-path path/to/theme.json` or `--theme-name "Aurora Group__NeutralAccent__Light__#118DFF"` (theme resolved under `theme_generator/themes/`). Optional `--run-generator` to run the theme generator first.
- **fetch_latest_theme_schema** — Fetch Power BI report theme JSON schema from Microsoft's powerbi-desktop-samples repo. Pinned version in `theme_generator/themes.config.json` (`reportThemeSchemaVersion`). Run `py theme_generator/tools/theme-agent/fetch_latest_theme_schema.py --update-pin` to fetch latest and update the pin. Validation and theme generator use the pinned schema when the cache exists.
- Wrapper scripts for common workflows (generate measures, validate TMDL, validate PBIP)
- \"Reproduce Aurora\" helpers (end-to-end local steps)
- Non-destructive utilities (format, lint, verify)

## Current sources (until we migrate)

- `_internal/tools/` (validation, generation, BPA, Power BI MCP)
- `theme_generator/` (theme generation; Power BI Theme Generator)

