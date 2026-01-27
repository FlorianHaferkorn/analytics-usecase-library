# Run All Checks Report

- Timestamp: 2026-01-27T08:09:06
- Repo: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library
- UseCasesRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases
- FactsheetsRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases\core
- KpiCatalogRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog
- DistRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist
- Transcript: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\_internal\reviews\run_all_checks_transcript.txt

## Summary

- Total checks: 26
- Failed checks: 2

## Checks

| Check | Status | Duration (s) | Arguments | Error |
| --- | --- | ---: | --- | --- |
| _internal/tools/validation/validate_factsheets.ps1 | ok | 1.01 |  |  |
| _internal/tools/validation/validate_kpi_catalog.ps1 | ok | 0.35 |  |  |
| _internal/tools/validation/check_factsheet_vs_kpi.ps1 | ok | 1.52 |  |  |
| _internal/tools/validation/check_measures_vs_kpi.ps1 | ok | 0.22 |  |  |
| _internal/tools/maintenance/check_docs_refs.ps1 | ok | 7.24 |  |  |
| _internal/tools/validation/check_docs_kpi_refs.ps1 | ok | 0.25 |  |  |
| _internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1 | ok | 0.13 |  |  |
| _internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1 | ok | 1.09 |  |  |
| _internal/tools/validation/check_duplicate_ids.ps1 | ok | 0.59 |  |  |
| _internal/tools/validation/check_forbidden_content.ps1 | ok | 0.37 |  |  |
| _internal/tools/validation/check_ssot_markers.ps1 | ok | 2.27 |  |  |
| _internal/tools/validation/check_docs_usecase_refs.ps1 | ok | 0.26 |  |  |
| _internal/tools/validation/check_action_codes_vs_kpi.ps1 | ok | 0.55 |  |  |
| _internal/tools/validation/check_factsheet_action_codes.ps1 | ok | 0.55 |  |  |
| _internal/tools/validation/check_usecase_actioncode_map.ps1 | ok | 0.52 |  |  |
| _internal/tools/validation/check_decision_spines.ps1 | ok | 0.47 |  |  |
| _internal/tools/validation/check_factsheet_actioncode_map.ps1 | ok | 0.14 |  |  |
| _internal/tools/validation/check_factsheet_layout.ps1 | ok | 1.79 |  |  |
| _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1 | failed | 0.43 | -KpiCatalogRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains | Non-zero exit code: 1 |
| _internal/tools/validation/check_dax_vs_measure_dictionary.ps1 | failed | 0.55 |  | Non-zero exit code: 1 |
| _internal/tools/validation/check_measure_dictionary_vs_gold.ps1 | ok | 0.17 | -GoldRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\data_contracts\domains -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains |  |
| _internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1 | ok | 0.04 | -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains -DistRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist |  |
| _internal/tools/validation/check_mojibake.ps1 | ok | 4.04 |  |  |
| _internal/tools/validation/check_markdownlint.ps1 | ok | 1.89 |  |  |
| _internal/tools/validation/check_yaml_format.ps1 | ok | 21.22 |  |  |
| _internal/tools/validation/check_schema_validation.ps1 | ok | 1.84 |  |  |

## Detailed Output

### _internal/tools/validation/validate_factsheets.ps1

```text
FactSheet validation passed.

```

### _internal/tools/validation/validate_kpi_catalog.ps1

```text
KPI Catalog validation passed.

```

### _internal/tools/validation/check_factsheet_vs_kpi.ps1

```text
Scanning Business/Technical Factsheets in C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases ...

UseCase                            Measure                            Covered
-------                            -------                            -------
COM-001_Sales_Performance          margin.gm.pct                         True
COM-001_Sales_Performance          sales.net_sales.amount                True
COM-001_Sales_Performance          sales.net_sales.delta_pct.ly          True
COM-001_Sales_Performance          sales.net_sales.delta_pct.plan        True
COM-001_Sales_Performance          sales.pvm.mix_effect.amount           True
COM-001_Sales_Performance          sales.pvm.price_effect.amount         True
COM-001_Sales_Performance          sales.pvm.volume_effect.amount        True
COM-002_Margin_Price_Performance   cost.cogs_per_unit.amount             True
COM-002_Margin_Price_Performance   margin.gm.amount                      True
COM-002_Margin_Price_Performance   margin.gm.pct                         True
COM-002_Margin_Price_Performance   margin.gm.vs_plan.pct                 True
COM-002_Margin_Price_Performance   profit.gross_margin                   True
COM-002_Margin_Price_Performance   sales.price.realization_pct           True
COM-002_Margin_Price_Performance   sales.pvm.mix_effect.amount           True
COM-003_Customer_Value             crm.active_customers.count            True
COM-003_Customer_Value             crm.churned_customers.count           True
COM-003_Customer_Value             crm.clv.amount                        True
COM-003_Customer_Value             crm.complaint.count                   True
COM-003_Customer_Value             crm.lifetime_revenue.amount           True
COM-003_Customer_Value             crm.nps.index                         True
COM-003_Customer_Value             crm.retention.pct                     True
COM-003_Customer_Value             crm.revenue_at_risk.amount            True
COM-004_Promotion_Effectiveness    margin.promo.gm.pct                   True
COM-004_Promotion_Effectiveness    sales.price.realization_pct           True
COM-004_Promotion_Effectiveness    sales.promo.cannibalization.pct       True
COM-004_Promotion_Effectiveness    sales.promo.incremental.amount        True
COM-004_Promotion_Effectiveness    sales.promo.roi.pct                   True
FIN-001_Cash_Liquidity_Performance fin.cash.balance                      True
FIN-001_Cash_Liquidity_Performance fin.cash.ocf                          True
FIN-001_Cash_Liquidity_Performance fin.cash.vs_plan.pct                  True
FIN-001_Cash_Liquidity_Performance scm.service_level.pct                 True
FIN-001_Cash_Liquidity_Performance scm.supplier_risk.score               True
FIN-001_Cash_Liquidity_Performance wc.ccc.days                           True
FIN-001_Cash_Liquidity_Performance wc.dio.days                           True
FIN-001_Cash_Liquidity_Performance wc.dpo.days                           True
FIN-001_Cash_Liquidity_Performance wc.dso.days                           True
FIN-002_Cost_Performance           cost.base_volume.amount               True
FIN-002_Cost_Performance           cost.material.pct                     True
FIN-002_Cost_Performance           cost.opex.base.amount                 True
FIN-002_Cost_Performance           cost.opex.vs_plan.pct                 True
FIN-002_Cost_Performance           cost.unit.amount                      True
FIN-002_Cost_Performance           margin.cogs.pct                       True
FIN-002_Cost_Performance           ops.labor.productivity.pct            True
FIN-002_Cost_Performance           ops.production.volume                 True
FIN-002_Cost_Performance           ops.quality.defect_rate.pct           True
FIN-002_Cost_Performance           ops.service_level.pct                 True
FIN-002_Cost_Performance           ops.yield.pct                         True
OPS-001_Operations_Performance     ops.availability.pct                  True
OPS-001_Operations_Performance     ops.downtime.pct                      True
OPS-001_Operations_Performance     ops.oee.pct                           True
OPS-001_Operations_Performance     ops.performance.pct                   True
OPS-001_Operations_Performance     ops.planned_output.units              True
OPS-001_Operations_Performance     ops.quality.pct                       True
OPS-001_Operations_Performance     ops.throughput.units                  True
OPS-002_Asset_Performance          ops.availability.pct                  True
OPS-002_Asset_Performance          ops.downtime.unplanned.pct            True
OPS-002_Asset_Performance          ops.failure.count                     True
OPS-002_Asset_Performance          ops.inventory.value.amount            True
OPS-002_Asset_Performance          ops.mtbf.hours                        True
OPS-002_Asset_Performance          ops.mttr.hours                        True
OPS-002_Asset_Performance          ops.pm.task.count                     True
OPS-002_Asset_Performance          ops.pm_compliance.pct                 True
OPS-002_Asset_Performance          ops.safety.incident.count             True
OPS-002_Asset_Performance          ops.spare_parts.stockout.pct          True
OPS-003_Quality_Yield              ops.planned_output.units              True
OPS-003_Quality_Yield              quality.complaint.pct                 True
OPS-003_Quality_Yield              quality.copq.amount                   True
OPS-003_Quality_Yield              quality.defect_density                True
OPS-003_Quality_Yield              quality.fpy.pct                       True
OPS-003_Quality_Yield              quality.rework.pct                    True
OPS-003_Quality_Yield              quality.scrap.pct                     True
OPS-003_Quality_Yield              sales.units                           True
SCM-001_Inventory_Performance      inv.dio.days                          True
SCM-001_Inventory_Performance      inv.obsolete.pct                      True
SCM-001_Inventory_Performance      inv.stockout.pct                      True
SCM-001_Inventory_Performance      inv.turnover                          True
SCM-001_Inventory_Performance      plan.forecast.accuracy.pct            True
SCM-001_Inventory_Performance      sales.units                           True
SCM-001_Inventory_Performance      supply.otif.pct                       True
SCM-002_Supply_Reliability_OTIF    order.lines                           True
SCM-002_Supply_Reliability_OTIF    shipments.count                       True
SCM-002_Supply_Reliability_OTIF    supply.expedite.amount                True
SCM-002_Supply_Reliability_OTIF    supply.in_full.pct                    True
SCM-002_Supply_Reliability_OTIF    supply.on_time.pct                    True
SCM-002_Supply_Reliability_OTIF    supply.otif.pct                       True
SCM-002_Supply_Reliability_OTIF    supply.penalty.amount                 True
SCM-002_Supply_Reliability_OTIF    supply.stockout_impact.pct            True
SCM-003_Forecast_vs_Actual         order.lines                           True
SCM-003_Forecast_vs_Actual         plan.forecast.accuracy.pct            True
SCM-003_Forecast_vs_Actual         plan.forecast.bias.pct                True
SCM-003_Forecast_vs_Actual         plan.forecast.mape.pct                True
SCM-003_Forecast_vs_Actual         plan.forecast.service_impact.pct      True
SCM-003_Forecast_vs_Actual         plan.replan.count                     True
SCM-003_Forecast_vs_Actual         plans.count                           True
SCM-003_Forecast_vs_Actual         sales.units                           True
XD-001_Service_Level_Performance   svc.aht.minutes                       True
XD-001_Service_Level_Performance   svc.backlog.count                     True
XD-001_Service_Level_Performance   svc.escalation.pct                    True
XD-001_Service_Level_Performance   svc.fcr.pct                           True
XD-001_Service_Level_Performance   svc.nps.index                         True
XD-001_Service_Level_Performance   svc.sla.attainment.pct                True
XD-001_Service_Level_Performance   svc.tickets.closed.count              True
XD-001_Service_Level_Performance   svc.tickets.created.count             True
XD-002_Resource_Utilization        res.occupancy.pct                     True
XD-002_Resource_Utilization        res.overtime.pct                      True
XD-002_Resource_Utilization        res.shrinkage.pct                     True
XD-002_Resource_Utilization        res.utilization.pct                   True
XD-002_Resource_Utilization        svc.backlog.count                     True
XD-002_Resource_Utilization        svc.sla.attainment.pct                True
XD-002_Resource_Utilization        svc.tickets.created.count             True
XD-003_Executive_KPI_Overview      crm.clv.amount                        True
XD-003_Executive_KPI_Overview      enterprise.action_outcome_rate.pct    True
XD-003_Executive_KPI_Overview      enterprise.action_routed.count        True
XD-003_Executive_KPI_Overview      enterprise.value_at_risk.index        True
XD-003_Executive_KPI_Overview      margin.gm.pct                         True
XD-003_Executive_KPI_Overview      ops.otif.pct                          True
XD-003_Executive_KPI_Overview      ops.working_capital.ccc.days          True
XD-003_Executive_KPI_Overview      people.attrition_risk.pct             True
XD-003_Executive_KPI_Overview      people.digital_adoption.pct           True
XD-003_Executive_KPI_Overview      sales.net_sales.delta_pct.ly          True
XD-003_Executive_KPI_Overview      svc.sla.attainment.pct                True
All required measures are covered in KPI Catalog.

```

### _internal/tools/validation/check_measures_vs_kpi.ps1

```text
Checking measures vs KPI catalogs...
  Dist root:      C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist
  KPI catalog:    C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog
No _Measures.tmdl files found under dist.

```

### _internal/tools/maintenance/check_docs_refs.ps1

```text
Checking documentation and tooling references...
  OK   docs/README.md (Docs overview)
  OK   docs/company/company_strategy.md (Business Strategy / Strategic KPIs / Alignment Map (canonical))
  OK   docs/operating_model/semantic_layer.md (Semantic Layer blueprint)
  OK   docs/operating_model/distribution_architecture.md (Distribution architecture)
  OK   usecases/templates/usecase_factsheet_business.md (Use Case factsheet (business) template)
  OK   usecases/templates/usecase_factsheet_technical.md (Use Case factsheet (technical) template)
  OK   usecases/UseCase_Inventory.md (Use Case Inventory)
  OK   framework/templates/KPI_Catalog_templates/KPI_Catalog_SCHEMA.md (KPI Catalog Schema (canonical))
  OK   framework/kpi_catalog/README.md (KPI Catalog overview)
  OK   _internal/tools/run_all_checks.ps1 (Run all checks script)
  OK   _internal/tools/generation/new_usecase.ps1 (New usecase helper)
  OK   _internal/tools/generation/generate_tmdl_measures.ps1 (TMDL measures generator)
  OK   _internal/tools/generation/generate_all_measures.ps1 (Generate all measures wrapper)

Documentation and tooling references look consistent.

```

### _internal/tools/validation/check_docs_kpi_refs.ps1

```text
Docs -> KPI Catalog consistency
OK: docs KPI references are consistent.

```

### _internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1

```text
UseCase Inventory <-> Factsheets consistency
OK: inventory and factsheets are consistent.

```

### _internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1

```text
KPI Catalog -> Factsheets coverage
Note: This list checks core factsheets, core action codes, inventory mentions, and measure dictionaries.
It does not consider KPI aliases or KPIs used only as intermediate inputs.
Coverage counts (unique KPI IDs):
  Factsheets:           104
  Inventory:            81
  Core Action Codes:    61
  Measure Dictionaries: 108
  Total covered:        111
OK: all KPI IDs are referenced in factsheets.

```

### _internal/tools/validation/check_duplicate_ids.ps1

```text
OK: no duplicate IDs detected.

```

### _internal/tools/validation/check_forbidden_content.ps1

```text
OK: no forbidden content detected.

```

### _internal/tools/validation/check_ssot_markers.ps1

```text
OK: SSOT markers only in allowlisted files.

```

### _internal/tools/validation/check_docs_usecase_refs.ps1

```text
Docs -> UseCase references consistency
OK: docs use case references are consistent.

```

### _internal/tools/validation/check_action_codes_vs_kpi.ps1

```text
Action Codes -> KPI Catalog consistency
OK: action code KPI references are consistent.

```

### _internal/tools/validation/check_factsheet_action_codes.ps1

```text
Factsheets -> Action Codes consistency
OK: factsheet action codes are consistent.

```

### _internal/tools/validation/check_usecase_actioncode_map.ps1

```text
UseCase ActionCode map consistency
OK: UseCase ActionCode map is consistent with core and action codes.

```

### _internal/tools/validation/check_decision_spines.ps1

```text
Decision Spine map consistency
Decision Spine content validation
OK: Decision Spines map matches core use cases and files.

```

### _internal/tools/validation/check_factsheet_actioncode_map.ps1

```text
Factsheets -> ActionCode map alignment
OK: factsheet action_codes align with the UseCase ActionCode map.

```

### _internal/tools/validation/check_factsheet_layout.ps1

```text
Template layout checks
Note: no measure documents found for template at C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\templates\measure_templates\measure_template.md (no instances under semantic_models/measures).
Note: no page instance documents found for templates under C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\templates\page_templates\page_types.
Layout mismatches found:
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description
- [kpi_catalog_technical] C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog\KPI_Catalog.md
  Extra: formatString; description

```

### _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1

```text
KPI Catalog <-> Measure Dictionary consistency
Missing in Measure Dictionaries (present in KPI catalogs):
  - fin.liquidity.inventory.amount
  - fin.liquidity.payables.amount
  - ops.planned.hours

```

### _internal/tools/validation/check_dax_vs_measure_dictionary.ps1

```text
DAX definitions vs Measure Dictionaries
OK: all DAX measures are present in their Measure Dictionaries.

```

### _internal/tools/validation/check_measure_dictionary_vs_gold.ps1

```text
Measure Dictionary -> Gold Data Contracts consistency
OK: all referenced tables/columns exist in gold contracts.

```

### _internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1

```text
No _Measures.tmdl files found under dist. Skipping TMDL check.

```

### _internal/tools/validation/check_mojibake.ps1

```text
Mojibake scan
Potential mojibake found:
  - framework\templates\kpi_catalog_templates\kpi_catalog_SCHEMA.md:62: DAX format string for display formatting, e.g. `"#,0"`, `"#,0.0%"`, `"â‚¬#,0.00"`.
  - _internal\tools\maintenance\add_missing_kpis.ps1:253: # Finde EinfÃ¼gepunkt (nach wc.dso.days)
  - _internal\tools\maintenance\add_missing_kpis.ps1:258: # Finde das Ende des wc.dso.days Blocks (nÃ¤chstes "- kpi_id:" oder Ende)
  - _internal\tools\maintenance\add_missing_kpis.ps1:266: # Am Ende einfÃ¼gen
  - _internal\tools\maintenance\add_missing_metadata.ps1:92: # Regex Pattern fÃ¼r diesen KPI Block
  - _internal\vision\framework_evolution.md:10: Define the long-term direction of the Analytics Framework and the smallest, pragmatic steps to reach itâ€”without creating customer-facing promises or locking into specific tools.
  - _internal\vision\framework_evolution.md:73: ### V1 â€” Foundation (Current Baseline)
  - _internal\vision\framework_evolution.md:77: - Core framework artifacts exist (strategy â†’ KPIs â†’ use cases â†’ action codes â†’ templates).
  - _internal\vision\framework_evolution.md:92: ### V2 â€” Assisted Quality (Soft Review + Authoring Assist)
  - _internal\vision\framework_evolution.md:114: ### V3 â€” Guided Automation (Template Instantiation + Partial Closed Loop)
  - _internal\vision\framework_evolution.md:137: ### V4 â€” Assisted Operations (Observability + Recommendations at Scale)
  - _internal\vision\framework_evolution.md:154: ### V5 â€” Assisted Consumption (Conversational Layer on Semantic)
  - _internal\vision\framework_evolution.md:160: - guided exploration (â€œwhy did margin drop?â€) using governed measures only
  - _internal\vision\framework_evolution.md:168: - â€œExplainabilityâ€ remains aligned with governed artifacts.
  - _internal\vision\framework_evolution.md:172: ### V6 â€” Orchestrated Autonomy (Vision)
  - _internal\vision\framework_evolution.md:189: ## Practical â€œHow We Get Thereâ€ (Concrete Steps)
  - _internal\vision\framework_evolution.md:191: ### Step 1 â€” Freeze V1 + Deliver Aurora Group
  - _internal\vision\framework_evolution.md:196: ### Step 2 â€” Introduce Stage 2 Soft Review as a Non-Blocker
  - _internal\vision\framework_evolution.md:197: - Start with â€œdiff-onlyâ€ and â€œmax 10 findingsâ€.
  - _internal\vision\framework_evolution.md:200: ### Step 3 â€” Automate Scaffolding, Not Decisions
  - _internal\vision\framework_evolution.md:204: ### Step 4 â€” Standardize Operations Before AI Consumption
  - _internal\vision\framework_evolution.md:208: ### Step 5 â€” Add Conversational Consumption Only After Semantic Maturity
  - _internal\vision\framework_evolution.md:210: - No â€œcreative analyticsâ€ in production contexts.

```

### _internal/tools/validation/check_markdownlint.ps1

```text
Markdownlint check


```

### _internal/tools/validation/check_yaml_format.ps1

```text
YAML format check
PS>TerminatingError(python.exe): "Der ausgeführte Befehl wurde beendet, da die Einstellungsvariable "ErrorActionPreference" oder ein allgemeiner Parameter auf "Stop" festgelegt ist: Python wurde nicht gefunden; ohne Argumente ausf³hren, um aus dem Microsoft Store zu installieren, oder deaktivieren Sie diese Verkn³pfung unter "Einstellungen > Apps > Erweiterte App-Einstellungen > App-Ausf³hrungsaliase".."




















































































































OK: All YAML files parsed successfully.

```

### _internal/tools/validation/check_schema_validation.ps1

```text
Schema validation



OK: schema validation passed.

**********************
Ende der Windows PowerShell-Aufzeichnung
Endzeit: 20260127080905
**********************
```
