# Run All Checks Status

- Timestamp: 2026-01-15T12:01:05
- Repo: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library
- UseCasesRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases
- KpiCatalogRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog
- DistRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist
- Transcript: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\_internal\reviews\run_all_checks_transcript.txt

## Summary

- Total checks: 16
- Failed checks: 0

## Checks

| Check | Status | Duration (s) | Arguments | Error |
| --- | --- | ---: | --- | --- |
| _internal/tools/validation/validate_factsheets.ps1 | ok | 0.15 |  |  |
| _internal/tools/validation/validate_kpi_catalog.ps1 | ok | 0.49 |  |  |
| _internal/tools/validation/check_factsheet_vs_kpi.ps1 | ok | 2.22 |  |  |
| _internal/tools/validation/check_measures_vs_kpi.ps1 | ok | 0.33 |  |  |
| _internal/tools/maintenance/check_docs_refs.ps1 | ok | 0.11 |  |  |
| _internal/tools/validation/check_docs_kpi_refs.ps1 | ok | 1.33 |  |  |
| _internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1 | ok | 0.29 |  |  |
| _internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1 | ok | 0.85 |  |  |
| _internal/tools/validation/check_docs_usecase_refs.ps1 | ok | 0.38 |  |  |
| _internal/tools/validation/check_action_codes_vs_kpi.ps1 | ok | 3.61 |  |  |
| _internal/tools/validation/check_factsheet_action_codes.ps1 | ok | 0.52 |  |  |
| _internal/tools/validation/check_factsheet_layout.ps1 | ok | 2.57 |  |  |
| _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1 | ok | 1.36 | -KpiCatalogRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains |  |
| _internal/tools/validation/check_dax_vs_measure_dictionary.ps1 | ok | 0.59 |  |  |
| _internal/tools/validation/check_measure_dictionary_vs_gold.ps1 | ok | 0.24 | -GoldRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\data_contracts\domains -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains |  |
| _internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1 | ok | 0.09 | -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains -DistRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist |  |
