# PBIR JSON Schema Cache

| Path | Purpose |
|---|---|
| `microsoft/` | Official Microsoft Fabric schemas (fetched from GitHub). Used by `check_pbir_schema.ps1` via each file's `$schema` URL. |
| `*.schema.json` (root) | Legacy structural stubs (2.3.0 / 2.0.0). Used only when a JSON file has no `$schema` field. |
| `schema_manifest.json` | Pinned versions from `schema_registry.py` (generator SSOT). |

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
