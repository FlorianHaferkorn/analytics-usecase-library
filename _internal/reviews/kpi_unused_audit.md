# KPI Unused Audit (a-d)

Generated: 2026-01-15 14:52:18

Criteria:
- a) Needed for measures referenced in core factsheets (via measure dependencies)
- b) Missing in factsheets or irrelevant (manual review)
- c) Required by Action Codes referenced in core factsheets
- d) Likely duplicate/alias of a KPI already used in factsheets

Total unused KPIs (not in factsheets): 104
A: 0 | B: 7 | C: 97 | D: 7

## A) Needed for measures referenced in factsheets

- (none)

## B) Missing in factsheets / review relevance

- margin.cogs.pct
- ops.otif.pct
- ops.working_capital.ccc.days
- people.digital_adoption.pct
- profit.gross_margin
- sales.pvm.volume_effect.amount
- svc.nps.index

## C) Required by Action Codes used in core factsheets

- cost.base_volume.amount
- cost.cogs_per_unit.amount
- cost.material.pct
- cost.opex.base.amount
- cost.opex.vs_plan.pct
- cost.unit.amount
- crm.active_customers.count
- crm.churned_customers.count
- crm.clv.amount
- crm.complaint.count
- crm.lifetime_revenue.amount
- crm.nps.index
- crm.retention.pct
- crm.revenue_at_risk.amount
- enterprise.action_outcome_rate.pct
- enterprise.action_routed.count
- enterprise.value_at_risk.index
- fin.cash.balance
- fin.cash.ocf
- fin.cash.vs_plan.pct
- inv.dio.days
- inv.obsolete.pct
- inv.stockout.pct
- inv.turnover
- margin.gm.amount
- margin.gm.pct
- margin.gm.vs_plan.pct
- margin.promo.gm.pct
- ops.availability.pct
- ops.downtime.pct
- ops.downtime.unplanned.pct
- ops.failure.count
- ops.inventory.value.amount
- ops.labor.productivity.pct
- ops.mtbf.hours
- ops.mttr.hours
- ops.oee.pct
- ops.performance.pct
- ops.planned_output.units
- ops.pm.task.count
- ops.pm_compliance.pct
- ops.production.volume
- ops.quality.defect_rate.pct
- ops.quality.pct
- ops.safety.incident.count
- ops.service_level.pct
- ops.spare_parts.stockout.pct
- ops.throughput.units
- ops.yield.pct
- order.lines
- people.attrition_risk.pct
- plan.forecast.accuracy.pct
- plan.forecast.bias.pct
- plan.forecast.mape.pct
- plan.forecast.service_impact.pct
- plan.replan.count
- plans.count
- quality.complaint.pct
- quality.copq.amount
- quality.defect_density
- quality.fpy.pct
- quality.rework.pct
- quality.scrap.pct
- res.occupancy.pct
- res.overtime.pct
- res.shrinkage.pct
- res.utilization.pct
- sales.net_sales.amount
- sales.net_sales.delta_pct.ly
- sales.net_sales.delta_pct.plan
- sales.price.realization_pct
- sales.promo.cannibalization.pct
- sales.promo.incremental.amount
- sales.promo.roi.pct
- sales.pvm.mix_effect.amount
- sales.pvm.price_effect.amount
- sales.units
- scm.service_level.pct
- scm.supplier_risk.score
- shipments.count
- supply.expedite.amount
- supply.in_full.pct
- supply.on_time.pct
- supply.otif.pct
- supply.penalty.amount
- supply.stockout_impact.pct
- svc.aht.minutes
- svc.backlog.count
- svc.escalation.pct
- svc.fcr.pct
- svc.sla.attainment.pct
- svc.tickets.closed.count
- svc.tickets.created.count
- wc.ccc.days
- wc.dio.days
- wc.dpo.days
- wc.dso.days

## D) Likely duplicates / aliases of used KPIs

- crm.complaint.rate.pct -> quality.complaint.pct
- Delta% Net Sales -> sales.net_sales.delta_pct.ly
- fin.liquidity.cash_conversion_cycle_days -> ops.working_capital.ccc.days
- fin.liquidity.operating_cash_flow -> fin.cash.ocf
- hr.gm.amount -> margin.gm.amount
- ops.inventory.turnover -> inv.turnover
- sales.forecast.bias_pct -> plan.forecast.bias.pct

Notes:
- Section C uses all Action Codes (not only those referenced by core factsheets).
- Section D lists alias mappings from KPI catalogs (alias -> kpi_id).
