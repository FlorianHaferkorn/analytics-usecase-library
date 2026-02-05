# Fabric/Power BI validation

Fabric-specific checks run by `run_fabric_checks.ps1` and (Fabric-related steps) by `run_all_checks.ps1`.

| Script | Purpose |
|--------|---------|
| `check_tmdl_syntax.ps1` | TMDL files: tabs-only indentation (error), no `description:` property (error). See `implementations/microsoft_fabric_powerbi/guide/tmdl_best_practices.md`. |
| `check_tmdl_pbip_readiness.ps1` | PBIP load readiness: no duplicate relationship IDs, no duplicate measure names, RLS uses `securityFilteringBehavior: oneDirection`, partition Source uses parameter (e.g. GoldDataPath) not hardcoded path. |
| `check_measures_vs_kpi.ps1` | KPI IDs referenced in _Measures.tmdl exist in framework/kpi_catalog. |
| `check_tmdl_vs_measure_dictionary.ps1` | TMDL measure names align with framework semantic_models measure dictionaries. |
| `check_dax_best_practices.ps1` | DAX in _Measures.tmdl conforms to rules in `_internal/tools/linters/powerbi/bpa-rules-dax.json` (DIVIDE, VAR/RETURN, no FORMAT, etc.). |

Run from repository root. DistRoot defaults to `implementations/microsoft_fabric_powerbi/dist`.
