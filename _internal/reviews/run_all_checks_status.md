# Run All Checks Status

- Timestamp: 2026-01-15T20:02:20
- Repo: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library
- UseCasesRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases
- FactsheetsRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases\core
- KpiCatalogRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog
- DistRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist
- Transcript: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\_internal\reviews\run_all_checks_transcript.txt

## Summary

- Total checks: 16
- Failed checks: 2

## Checks

| Check | Status | Duration (s) | Arguments | Error |
| --- | --- | ---: | --- | --- |
| _internal/tools/validation/validate_factsheets.ps1 | ok | 0.12 |  |  |
| _internal/tools/validation/validate_kpi_catalog.ps1 | ok | 0.5 |  |  |
| _internal/tools/validation/check_factsheet_vs_kpi.ps1 | ok | 2.78 |  |  |
| _internal/tools/validation/check_measures_vs_kpi.ps1 | ok | 0.33 |  |  |
| _internal/tools/maintenance/check_docs_refs.ps1 | ok | 0.12 |  |  |
| _internal/tools/validation/check_docs_kpi_refs.ps1 | ok | 0.53 |  |  |
| _internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1 | ok | 0.24 |  |  |
| _internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1 | ok | 0.98 |  |  |
| _internal/tools/validation/check_docs_usecase_refs.ps1 | ok | 0.36 |  |  |
| _internal/tools/validation/check_action_codes_vs_kpi.ps1 | ok | 0.61 |  |  |
| _internal/tools/validation/check_factsheet_action_codes.ps1 | ok | 0.6 |  |  |
| _internal/tools/validation/check_factsheet_layout.ps1 | ok | 1.95 |  |  |
| _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1 | failed | 0.62 | -KpiCatalogRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains | Non-zero exit code: 1 |
| _internal/tools/validation/check_dax_vs_measure_dictionary.ps1 | failed | 0.61 |  | Non-zero exit code: 1 |
| _internal/tools/validation/check_measure_dictionary_vs_gold.ps1 | ok | 0.32 | -GoldRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\data_contracts\domains -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains |  |
| _internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1 | ok | 0.12 | -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains -DistRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist |  |
