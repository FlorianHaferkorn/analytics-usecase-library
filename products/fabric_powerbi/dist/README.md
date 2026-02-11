# dist (Fabric/Power BI implementation output)

Default **output folder** for Fabric/Power BI–related generated artifacts (e.g. `_Measures.tmdl` from `generate_tmdl_measures.ps1`).

- **Used by** `run_all_checks.ps1` and `run_fabric_checks.ps1`: scripts under `products/fabric_powerbi/tooling/validation/` (check_measures_vs_kpi, check_tmdl_vs_measure_dictionary, check_dax_best_practices) expect this path.
- All generation and checks that consume TMDL/measures output reference `products/fabric_powerbi/dist` only.
- Optional: add `products/fabric_powerbi/dist/` to `.gitignore` if you prefer not to commit generated artifacts.
