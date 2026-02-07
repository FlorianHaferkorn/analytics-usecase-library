# Missing DAX Expression Audit

Generated: 2026-02-06

## Summary

- Total KPIs audited: 93
- KPIs with DAX: 28
- KPIs missing DAX: 65
- KPIs not in catalog: 0

## By Use Case

### COM-001

- Total KPIs: 7
- With DAX: 7
- Missing DAX: 0


### COM-002

- Total KPIs: 6
- With DAX: 6
- Missing DAX: 0


### COM-003

- Total KPIs: 8
- With DAX: 7
- Missing DAX: 1

**Missing DAX:**
- `crm.nps.index` (missing_dax)


### COM-004

- Total KPIs: 5
- With DAX: 5
- Missing DAX: 0


### FIN-001

- Total KPIs: 7
- With DAX: 0
- Missing DAX: 7

**Missing DAX:**
- `fin.cash.balance` (missing_dax)
- `fin.cash.ocf` (missing_dax)
- `fin.cash.vs_plan.pct` (missing_dax)
- `wc.ccc.days` (missing_dax)
- `wc.dso.days` (missing_dax)
- `wc.dio.days` (missing_dax)
- `wc.dpo.days` (missing_dax)


### FIN-002

- Total KPIs: 5
- With DAX: 0
- Missing DAX: 5

**Missing DAX:**
- `cost.unit.amount` (missing_dax)
- `margin.cogs.pct` (missing_dax)
- `cost.opex.vs_plan.pct` (missing_dax)
- `cost.material.pct` (missing_dax)
- `ops.labor.productivity.pct` (missing_dax)


### OPS-001

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `ops.oee.pct` (missing_dax)
- `ops.availability.pct` (missing_dax)
- `ops.performance.pct` (missing_dax)
- `ops.quality.pct` (missing_dax)
- `ops.throughput.units` (missing_dax)
- `ops.downtime.pct` (missing_dax)


### OPS-002

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `ops.availability.pct` (missing_dax)
- `ops.mtbf.hours` (missing_dax)
- `ops.mttr.hours` (missing_dax)
- `ops.downtime.unplanned.pct` (missing_dax)
- `ops.spare_parts.stockout.pct` (missing_dax)
- `ops.pm_compliance.pct` (missing_dax)


### OPS-003

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `quality.fpy.pct` (missing_dax)
- `quality.scrap.pct` (missing_dax)
- `quality.rework.pct` (missing_dax)
- `quality.copq.amount` (missing_dax)
- `quality.complaint.pct` (missing_dax)
- `quality.defect_density` (missing_dax)


### SCM-001

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `inv.dio.days` (missing_dax)
- `inv.turnover` (missing_dax)
- `inv.stockout.pct` (missing_dax)
- `supply.otif.pct` (missing_dax)
- `inv.obsolete.pct` (missing_dax)
- `plan.forecast.accuracy.pct` (missing_dax)


### SCM-002

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `supply.otif.pct` (missing_dax)
- `supply.on_time.pct` (missing_dax)
- `supply.in_full.pct` (missing_dax)
- `supply.stockout_impact.pct` (missing_dax)
- `supply.penalty.amount` (missing_dax)
- `supply.expedite.amount` (missing_dax)


### SCM-003

- Total KPIs: 5
- With DAX: 0
- Missing DAX: 5

**Missing DAX:**
- `plan.forecast.accuracy.pct` (missing_dax)
- `plan.forecast.mape.pct` (missing_dax)
- `plan.forecast.bias.pct` (missing_dax)
- `plan.forecast.service_impact.pct` (missing_dax)
- `plan.replan.count` (missing_dax)


### XD-001

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `svc.sla.attainment.pct` (missing_dax)
- `svc.fcr.pct` (missing_dax)
- `svc.aht.minutes` (missing_dax)
- `svc.backlog.count` (missing_dax)
- `svc.nps.index` (missing_dax)
- `svc.escalation.pct` (missing_dax)


### XD-002

- Total KPIs: 6
- With DAX: 0
- Missing DAX: 6

**Missing DAX:**
- `res.utilization.pct` (missing_dax)
- `res.occupancy.pct` (missing_dax)
- `svc.sla.attainment.pct` (missing_dax)
- `res.overtime.pct` (missing_dax)
- `res.shrinkage.pct` (missing_dax)
- `svc.backlog.count` (missing_dax)


### XD-003

- Total KPIs: 8
- With DAX: 3
- Missing DAX: 5

**Missing DAX:**
- `svc.sla.attainment.pct` (missing_dax)
- `ops.otif.pct` (missing_dax)
- `ops.working_capital.ccc.days` (missing_dax)
- `people.digital_adoption.pct` (missing_dax)
- `people.attrition_risk.pct` (missing_dax)


## Detailed Results

| Use Case | KPI ID | Status |
|----------|--------|--------|| COM-001 | `margin.gm.pct` | has_dax |
| COM-001 | `sales.net_sales.amount` | has_dax |
| COM-001 | `sales.net_sales.delta_pct.ly` | has_dax |
| COM-001 | `sales.net_sales.delta_pct.plan` | has_dax |
| COM-001 | `sales.pvm.mix_effect.amount` | has_dax |
| COM-001 | `sales.pvm.price_effect.amount` | has_dax |
| COM-001 | `sales.pvm.volume_effect.amount` | has_dax |
| COM-002 | `cost.cogs_per_unit.amount` | has_dax |
| COM-002 | `margin.gm.amount` | has_dax |
| COM-002 | `margin.gm.pct` | has_dax |
| COM-002 | `margin.gm.vs_plan.pct` | has_dax |
| COM-002 | `sales.price.realization_pct` | has_dax |
| COM-002 | `sales.pvm.mix_effect.amount` | has_dax |
| COM-003 | `crm.active_customers.count` | has_dax |
| COM-003 | `crm.churned_customers.count` | has_dax |
| COM-003 | `crm.clv.amount` | has_dax |
| COM-003 | `crm.complaint.count` | has_dax |
| COM-003 | `crm.lifetime_revenue.amount` | has_dax |
| COM-003 | `crm.nps.index` | missing_dax |
| COM-003 | `crm.retention.pct` | has_dax |
| COM-003 | `crm.revenue_at_risk.amount` | has_dax |
| COM-004 | `margin.promo.gm.pct` | has_dax |
| COM-004 | `sales.price.realization_pct` | has_dax |
| COM-004 | `sales.promo.cannibalization.pct` | has_dax |
| COM-004 | `sales.promo.incremental.amount` | has_dax |
| COM-004 | `sales.promo.roi.pct` | has_dax |
| FIN-001 | `fin.cash.balance` | missing_dax |
| FIN-001 | `fin.cash.ocf` | missing_dax |
| FIN-001 | `fin.cash.vs_plan.pct` | missing_dax |
| FIN-001 | `wc.ccc.days` | missing_dax |
| FIN-001 | `wc.dio.days` | missing_dax |
| FIN-001 | `wc.dpo.days` | missing_dax |
| FIN-001 | `wc.dso.days` | missing_dax |
| FIN-002 | `cost.material.pct` | missing_dax |
| FIN-002 | `cost.opex.vs_plan.pct` | missing_dax |
| FIN-002 | `cost.unit.amount` | missing_dax |
| FIN-002 | `margin.cogs.pct` | missing_dax |
| FIN-002 | `ops.labor.productivity.pct` | missing_dax |
| OPS-001 | `ops.availability.pct` | missing_dax |
| OPS-001 | `ops.downtime.pct` | missing_dax |
| OPS-001 | `ops.oee.pct` | missing_dax |
| OPS-001 | `ops.performance.pct` | missing_dax |
| OPS-001 | `ops.quality.pct` | missing_dax |
| OPS-001 | `ops.throughput.units` | missing_dax |
| OPS-002 | `ops.availability.pct` | missing_dax |
| OPS-002 | `ops.downtime.unplanned.pct` | missing_dax |
| OPS-002 | `ops.mtbf.hours` | missing_dax |
| OPS-002 | `ops.mttr.hours` | missing_dax |
| OPS-002 | `ops.pm_compliance.pct` | missing_dax |
| OPS-002 | `ops.spare_parts.stockout.pct` | missing_dax |
| OPS-003 | `quality.complaint.pct` | missing_dax |
| OPS-003 | `quality.copq.amount` | missing_dax |
| OPS-003 | `quality.defect_density` | missing_dax |
| OPS-003 | `quality.fpy.pct` | missing_dax |
| OPS-003 | `quality.rework.pct` | missing_dax |
| OPS-003 | `quality.scrap.pct` | missing_dax |
| SCM-001 | `inv.dio.days` | missing_dax |
| SCM-001 | `inv.obsolete.pct` | missing_dax |
| SCM-001 | `inv.stockout.pct` | missing_dax |
| SCM-001 | `inv.turnover` | missing_dax |
| SCM-001 | `plan.forecast.accuracy.pct` | missing_dax |
| SCM-001 | `supply.otif.pct` | missing_dax |
| SCM-002 | `supply.expedite.amount` | missing_dax |
| SCM-002 | `supply.in_full.pct` | missing_dax |
| SCM-002 | `supply.on_time.pct` | missing_dax |
| SCM-002 | `supply.otif.pct` | missing_dax |
| SCM-002 | `supply.penalty.amount` | missing_dax |
| SCM-002 | `supply.stockout_impact.pct` | missing_dax |
| SCM-003 | `plan.forecast.accuracy.pct` | missing_dax |
| SCM-003 | `plan.forecast.bias.pct` | missing_dax |
| SCM-003 | `plan.forecast.mape.pct` | missing_dax |
| SCM-003 | `plan.forecast.service_impact.pct` | missing_dax |
| SCM-003 | `plan.replan.count` | missing_dax |
| XD-001 | `svc.aht.minutes` | missing_dax |
| XD-001 | `svc.backlog.count` | missing_dax |
| XD-001 | `svc.escalation.pct` | missing_dax |
| XD-001 | `svc.fcr.pct` | missing_dax |
| XD-001 | `svc.nps.index` | missing_dax |
| XD-001 | `svc.sla.attainment.pct` | missing_dax |
| XD-002 | `res.occupancy.pct` | missing_dax |
| XD-002 | `res.overtime.pct` | missing_dax |
| XD-002 | `res.shrinkage.pct` | missing_dax |
| XD-002 | `res.utilization.pct` | missing_dax |
| XD-002 | `svc.backlog.count` | missing_dax |
| XD-002 | `svc.sla.attainment.pct` | missing_dax |
| XD-003 | `crm.clv.amount` | has_dax |
| XD-003 | `margin.gm.pct` | has_dax |
| XD-003 | `ops.otif.pct` | missing_dax |
| XD-003 | `ops.working_capital.ccc.days` | missing_dax |
| XD-003 | `people.attrition_risk.pct` | missing_dax |
| XD-003 | `people.digital_adoption.pct` | missing_dax |
| XD-003 | `sales.net_sales.delta_pct.ly` | has_dax |
| XD-003 | `svc.sla.attainment.pct` | missing_dax |

