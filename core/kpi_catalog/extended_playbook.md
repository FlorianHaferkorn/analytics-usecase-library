# Extended Playbook — Supporting KPIs (v1.0)

**Purpose:** This file catalogues the 93 supporting and narrow KPIs that complement the [Golden 20](golden_20.yaml) Lean Core spine. Each entry links back to its full definition in [KPI_Catalog.md](KPI_Catalog.md).

**Guidance:**
- These KPIs may be referenced in use case brackets as `influencing_kpi_ids`.
- They are not required in every report; use them when the use case demands deeper diagnostic depth.
- Registry builder reads both this file and `KPI_Catalog.md` — no measures are orphaned.
- Six KPIs marked `deprecated: true` below are candidates for removal in v1.1.

---

## Deprecated Orphans (v1.0 — removal target v1.1)

These KPIs have no active bracket or action code references. They will be removed after confirming no TMDL measures depend on them.

| kpi_id | Reason |
|---|---|
| `fin.liquidity.payables.amount` | Superseded by `wc.dpo.days`; no bracket reference |
| `ops.planned.hours` | Narrow ops metric; no use case or action code references |
| `cost.base_volume.amount` | Internal calculation input; not a reportable KPI |
| `cost.opex.base.amount` | Internal calculation input; not a reportable KPI |
| `plan.replan.count` | Activity metric; too narrow for strategic reporting |
| `enterprise.action_routed.count` | Replaced by `enterprise.action_outcome_rate.pct` as primary |

---

## Supporting KPIs by Domain

### Customer & Market

| kpi_id | Back-link |
|---|---|
| `crm.complaint.count` | [KPI_Catalog.md — crm.complaint.count](KPI_Catalog.md) |
| `crm.churned_customers.count` | [KPI_Catalog.md — crm.churned_customers.count](KPI_Catalog.md) |
| `crm.lifetime_revenue.amount` | [KPI_Catalog.md — crm.lifetime_revenue.amount](KPI_Catalog.md) |
| `crm.active_customers.count` | [KPI_Catalog.md — crm.active_customers.count](KPI_Catalog.md) |

### Commercial / Sales

| kpi_id | Back-link |
|---|---|
| `sales.price.list.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.price.net.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.price.realization_pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.pvm.mix_effect.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.pvm.price_effect.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.pvm.volume_effect.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.net_sales.delta_pct.ly` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.net_sales.delta_pct.plan` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.units` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.cost.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.incremental_gm.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.roi.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.cannibalized_sales.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.cannibalization.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.baseline_sales.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `sales.promo.incremental.amount` | [KPI_Catalog.md](KPI_Catalog.md) |

### Operations / Quality

| kpi_id | Back-link |
|---|---|
| `ops.quality.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.labor.productivity.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.mtbf.hours` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.mttr.hours` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.pm_compliance.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.spare_parts.stockout.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.throughput.units` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.oee.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.failure.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.availability.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.downtime.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.downtime.unplanned.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.working_capital.ccc.days` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.safety.incident.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `quality.scrap.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `quality.rework.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `quality.complaint.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `quality.defect_density` | [KPI_Catalog.md](KPI_Catalog.md) |

### Supply Chain / Demand Planning

| kpi_id | Back-link |
|---|---|
| `inv.obsolete.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `inv.turnover` | [KPI_Catalog.md](KPI_Catalog.md) |
| `supply.on_time.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `supply.in_full.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `supply.stockout_impact.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `supply.expedite.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `supply.penalty.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `plan.forecast.service_impact.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `plan.forecast.mape.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `scm.supplier_risk.score` | [KPI_Catalog.md](KPI_Catalog.md) |
| `order.lines` | [KPI_Catalog.md](KPI_Catalog.md) |
| `plans.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `shipments.count` | [KPI_Catalog.md](KPI_Catalog.md) |

### Finance / Working Capital

| kpi_id | Back-link |
|---|---|
| `wc.dso.days` | [KPI_Catalog.md](KPI_Catalog.md) |
| `wc.dio.days` | [KPI_Catalog.md](KPI_Catalog.md) |
| `wc.dpo.days` | [KPI_Catalog.md](KPI_Catalog.md) |
| `wc.ccc.days` | [KPI_Catalog.md](KPI_Catalog.md) |
| `fin.cash.balance` | [KPI_Catalog.md](KPI_Catalog.md) |
| `fin.cash.ocf` | [KPI_Catalog.md](KPI_Catalog.md) |
| `fin.cash.vs_plan.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `fin.liquidity.inventory.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `margin.promo.gm.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `margin.cogs.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `margin.gm.vs_plan.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `cost.cogs_per_unit.amount` | [KPI_Catalog.md](KPI_Catalog.md) |
| `cost.material.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `cost.opex.vs_plan.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `cost.unit.amount` | [KPI_Catalog.md](KPI_Catalog.md) |

### People / Resource

| kpi_id | Back-link |
|---|---|
| `people.digital_adoption.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `people.attrition_risk.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `res.utilization.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `res.occupancy.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `res.overtime.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `res.shrinkage.pct` | [KPI_Catalog.md](KPI_Catalog.md) |

### Service

| kpi_id | Back-link |
|---|---|
| `svc.sla.attainment.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `svc.aht.minutes` | [KPI_Catalog.md](KPI_Catalog.md) |
| `svc.backlog.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `svc.tickets.created.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `svc.tickets.closed.count` | [KPI_Catalog.md](KPI_Catalog.md) |

### Enterprise / Cross-Domain

| kpi_id | Back-link |
|---|---|
| `enterprise.action_outcome_rate.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
| `enterprise.value_at_risk.index` | [KPI_Catalog.md](KPI_Catalog.md) |

### Internal Calculation Inputs (narrow)

> These are referenced only as sub-components of other KPI measures. Consider consolidating into their parent measure definitions.

| kpi_id | Back-link |
|---|---|
| `ops.planned_output.units` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.pm.task.count` | [KPI_Catalog.md](KPI_Catalog.md) |
| `ops.quality.defect_rate.pct` | [KPI_Catalog.md](KPI_Catalog.md) |
