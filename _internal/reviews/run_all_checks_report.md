# Run All Checks Report

- Timestamp: 2026-01-15T16:56:51
- Repo: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library
- UseCasesRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases
- FactsheetsRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\usecases\core
- KpiCatalogRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog
- DistRoot: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist
- Status Report: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\_internal\reviews\run_all_checks_status.md
- Transcript: C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\_internal\reviews\run_all_checks_transcript.txt

## Summary

- Total checks: 16
- Failed checks: 2

## Checks

| Check | Status | Duration (s) | Arguments | Error |
| --- | --- | ---: | --- | --- |
| _internal/tools/validation/validate_factsheets.ps1 | ok | 0.16 |  |  |
| _internal/tools/validation/validate_kpi_catalog.ps1 | ok | 1.06 |  |  |
| _internal/tools/validation/check_factsheet_vs_kpi.ps1 | ok | 4.7 |  |  |
| _internal/tools/validation/check_measures_vs_kpi.ps1 | ok | 0.43 |  |  |
| _internal/tools/maintenance/check_docs_refs.ps1 | ok | 0.17 |  |  |
| _internal/tools/validation/check_docs_kpi_refs.ps1 | ok | 1.85 |  |  |
| _internal/tools/validation/check_usecase_inventory_vs_factsheets.ps1 | ok | 0.31 |  |  |
| _internal/tools/validation/check_kpi_catalog_unused_in_factsheets.ps1 | ok | 4.08 |  |  |
| _internal/tools/validation/check_docs_usecase_refs.ps1 | ok | 0.55 |  |  |
| _internal/tools/validation/check_action_codes_vs_kpi.ps1 | ok | 2.03 |  |  |
| _internal/tools/validation/check_factsheet_action_codes.ps1 | ok | 0.8 |  |  |
| _internal/tools/validation/check_factsheet_layout.ps1 | ok | 2.93 |  |  |
| _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1 | failed | 1.18 | -KpiCatalogRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\kpi_catalog -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains | Non-zero exit code: 1 |
| _internal/tools/validation/check_dax_vs_measure_dictionary.ps1 | failed | 0.71 |  | Non-zero exit code: 1 |
| _internal/tools/validation/check_measure_dictionary_vs_gold.ps1 | ok | 0.34 | -GoldRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\data_contracts\domains -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains |  |
| _internal/tools/validation/check_tmdl_vs_measure_dictionary.ps1 | ok | 0.12 | -MeasureDictRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\semantic_models\domains -DistRoot C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\dist |  |

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
  Core Action Codes:    55
  Measure Dictionaries: 104
  Total covered:        104
OK: all KPI IDs are referenced in factsheets.

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

### _internal/tools/validation/check_factsheet_layout.ps1

```text
Template layout checks
Note: no measure documents found for template at C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\templates\measure_templates\measure_template.md (no instances under semantic_models/measures).
Note: no page instance documents found for templates under C:\Users\florianhaferkorn\VSCode\analytics-usecase-library\framework\templates\page_templates\page_types.
OK: all checked documents match their template layout.

```

### _internal/tools/validation/check_kpi_vs_measure_dictionary.ps1

```text
KPI Catalog <-> Measure Dictionary consistency
Missing in KPI catalogs (present in Measure Dictionaries):
  - corp.benefit.realization.pct
  - corp.budget.adherence.pct
  - corp.payback.months
  - corp.project.roi.pct
  - corp.schedule.adherence.pct
  - cost.cogs.amount
  - crm.acquisition.cac.amount
  - crm.acquisition.conversion_rate.pct
  - crm.acquisition.conversions.count
  - crm.acquisition.leads.count
  - crm.active_customers_end.count
  - crm.active_customers_start.count
  - crm.at_risk_customers.count
  - crm.at_risk_share.pct
  - crm.basket_size.amount
  - crm.basket_size.units
  - crm.churn.pct
  - crm.complaint.rate.pct
  - crm.cross_sell_ratio.pct
  - crm.opportunities.open.amount
  - crm.opportunities.stage_conversion.pct
  - crm.opportunities.win_rate.pct
  - crm.opportunities.won.amount
  - crm.reactivated_customers.count
  - crm.reactivation.pct
  - esg.aligned_revenue.pct
  - esg.carbon_intensity.tco2e_per_revenue
  - esg.co2.total.tco2e
  - esg.energy.renewable_kwh
  - esg.energy.total_kwh
  - esg.ltifr.rate
  - fin.ebitda.amount
  - fin.liquidity.capex.amount
  - fin.liquidity.capex_ratio.pct
  - fin.liquidity.cash_conversion_cycle.delta_days
  - fin.liquidity.cash_conversion_cycle_days
  - fin.liquidity.dio_days_inventory_outstanding
  - fin.liquidity.dpo_days_payables_outstanding
  - fin.liquidity.dso_days_sales_outstanding
  - fin.liquidity.free_cash_flow
  - fin.liquidity.inventory.amount
  - fin.liquidity.operating_cash_flow
  - fin.liquidity.payables.amount
  - fin.liquidity.receivables.amount
  - fin.liquidity.working_capital
  - fin.risk.ead.amount
  - fin.risk.lgd.pct
  - fin.risk.pd.pct
  - gov.audit.findings.count
  - gov.audit.findings.open.count
  - gov.compliance.breach.count
  - gov.compliance.incidents.count
  - gov.data_quality.pct
  - gov.records.total.count
  - gov.valid_records.count
  - hr.absent_hours.amount
  - hr.absenteeism.pct
  - hr.exits.count
  - hr.fte.avg
  - hr.gm.amount
  - hr.gm_per_fte.amount
  - hr.headcount.avg
  - hr.personnel_cost.amount
  - hr.personnel_cost_ratio.pct
  - hr.revenue.amount
  - hr.revenue_per_fte.amount
  - hr.scheduled_hours.amount
  - hr.turnover.pct
  - margin.customer.amount
  - margin.customer.pct
  - margin.gm.channel_contribution.amount
  - margin.gm.delta_amount
  - margin.gm.delta_pct
  - margin.gm.plan.amount
  - market.share.relative.pct
  - market.share.total.pct
  - mkt.brand.awareness.pct
  - mkt.brand.preference.pct
  - ops.capacity.utilization.pct
  - ops.contract.compliance.pct
  - ops.deliveries.otif.count
  - ops.deliveries.total.count
  - ops.demand.total.qty
  - ops.demand.unfulfilled.qty
  - ops.downtime.hours
  - ops.inventory.days
  - ops.inventory.obsolescence.pct
  - ops.inventory.turnover
  - ops.logistics.cost_per_unit.amount
  - ops.logistics.cost_ratio.pct
  - ops.machine_downtime.pct
  - ops.order_accuracy.pct
  - ops.orders.correct.count
  - ops.orders.total.count
  - ops.planned.hours
  - ops.ppv.amount
  - ops.ppv.pct
  - ops.process.cost_per_unit.amount
  - ops.purchase.price.actual.amount
  - ops.purchase.price.contract.amount
  - ops.purchase.units.qty
  - ops.purchases.at_contract.amount
  - ops.purchases.total.amount
  - ops.replenishment.adherence.pct
  - ops.stockout.pct
  - ops.warehouse.cost_per_line.amount
  - ops.warehouse.lines_per_hour
  - ops.warehouse.picks_per_hour
  - ops.working_capital.ccc.delta_days
  - ops.working_capital.dio.days
  - ops.working_capital.dpo.days
  - ops.working_capital.dso.days
  - people.employee_engagement.pct
  - people.engaged_employees.count
  - people.innovation_rate.pct
  - people.survey_respondents.count
  - people.training_hours.amount
  - prod.contribution_margin.excl_mkt.pct
  - prod.contribution_margin.incl_mkt.pct
  - prod.lifecycle.age.months
  - prod.lifecycle.new_share.pct
  - prod.lifecycle.phase_distribution.pct
  - prod.roi.pct
  - profit.ebitda_margin
  - sales.baseline.amount
  - sales.customer.revenue_share.pct
  - sales.forecast.bias_pct
  - sales.forecast.mape_pct
  - sales.list_price.amount
  - sales.net_sales.amount.ly
  - sales.net_sales.channel_share.pct
  - sales.net_sales.delta_amount.ly
  - sales.promo.amount
  - sales.promo.uplift_pct
  - sales.revenue.growth_pct
  - sec.incident.count
  - sec.incident.critical.count
  - sec.incident.mttr.hours

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

**********************
Ende der Windows PowerShell-Aufzeichnung
Endzeit: 20260115165651
**********************
```
