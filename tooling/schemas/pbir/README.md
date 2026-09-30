# PBIR JSON Schema Cache

| Path | Purpose |
|---|---|
| `microsoft/` | Official Microsoft Fabric schemas (fetched from GitHub). Used by `check_pbir_schema.ps1` via each file's `$schema` URL. |
| `*.schema.json` (root) | Legacy structural stubs (2.3.0 / 2.0.0). Used only when a JSON file has no `$schema` field. |
| `schema_manifest.json` | Pinned versions from `schema_registry.py` (generator SSOT). |
| `base_themes/` | Base theme scaffolded by the pinned official CLI (D-587), vendored byte-for-byte by `refresh_authoring_metadata.py --base-theme-only`; constants in `tooling/report_quality/base_theme.py`, drift test `tooling/tests/test_base_theme_drift.py`. |

## Refresh cache

From repository root:

```powershell
py -3 products/fabric/powerbi/tooling/cache_pbir_schemas.py --scan-dist
```

Add `--force` to re-download all schemas. Run after bumping `$schema` versions in generated reports.

## Validate a report

```powershell
.\products\fabric\powerbi\tooling\validation\check_pbir_schema.ps1 `
  -ReportPath products/fabric/powerbi/dist/COM-001_Sales_Performance.Report
```
