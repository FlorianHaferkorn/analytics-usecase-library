# KPI Taxonomy (Reference View)

## Purpose

This document provides a **readable, domain-oriented view** of the KPI Catalog. It supports discovery, onboarding, and AI grounding. Authoritative definitions remain in `KPI_Catalog.md` and the catalog schema; this taxonomy is a summary only.

**Structure:** Domain → Topic (prefix) → KPI id and short purpose. **Used in** refers to core use case IDs.

---

## Commercial (COM)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| sales.net_sales.amount | Net revenue; core revenue control | COM-001, XD-003 |
| sales.net_sales.delta_pct.plan | Net Sales % vs Plan | COM-001 |
| sales.net_sales.delta_pct.ly | Net Sales % vs Last Year | COM-001, XD-003 |
| sales.pvm.price_effect.amount | Price effect on sales gap | COM-001 |
| sales.pvm.volume_effect.amount | Volume effect on sales gap | COM-001 |
| sales.pvm.mix_effect.amount | Mix effect on sales gap | COM-001, COM-002 |
| margin.gm.pct | Gross margin % | COM-001, COM-002, XD-003 |
| margin.gm.amount | Gross margin amount | COM-002 |
| margin.gm.vs_plan.pct | Gross margin % vs Plan | COM-002 |
| sales.price.realization_pct | Realized price vs list; discount leakage | COM-002, COM-004 |
| sales.promo.roi.pct | Promotion return on investment | COM-004 |
| sales.promo.incremental.amount | Incremental sales from promo | COM-004 |
| margin.promo.gm.pct | Gross margin % on promo | COM-004 |
| sales.promo.cannibalization.pct | Cannibalization from promo | COM-004 |

---

## Customer & CRM (COM-003, XD-003)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| crm.clv.amount | Customer lifetime value | COM-003, XD-003 |
| crm.lifetime_revenue.amount | Lifetime revenue per customer | COM-003 |
| crm.retention.pct | Customer retention rate | COM-003 |
| crm.churned_customers.count | Churned customers | COM-003 |
| crm.revenue_at_risk.amount | Revenue at risk from churn | COM-003 |
| crm.active_customers.count | Active customer count | COM-003 |
| crm.nps.index | Net Promoter Score | COM-003 |
| crm.complaint.count | Complaint count | COM-003 |

---

## Finance (FIN)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| fin.cash.balance | Cash balance | FIN-001 |
| fin.cash.ocf | Operating cash flow | FIN-001 |
| fin.cash.vs_plan.pct | Cash vs plan | FIN-001 |
| wc.ccc.days | Cash conversion cycle (days) | FIN-001, XD-003 |
| wc.dso.days | Days sales outstanding | FIN-001 |
| wc.dio.days | Days inventory outstanding | FIN-001 |
| wc.dpo.days | Days payables outstanding | FIN-001 |
| cost.unit.amount | Unit cost | FIN-002 |
| margin.cogs.pct | COGS % of revenue | FIN-002 |
| cost.opex.vs_plan.pct | OpEx vs plan | FIN-002 |
| cost.material.pct | Material cost share | FIN-002 |
| cost.cogs_per_unit.amount | COGS per unit | COM-002, FIN-002 |
| ops.labor.productivity.pct | Labor productivity | FIN-002 |

---

## Operations (OPS)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| ops.oee.pct | Overall equipment effectiveness | OPS-001 |
| ops.availability.pct | Availability % | OPS-001, OPS-002 |
| ops.performance.pct | Performance % | OPS-001 |
| ops.quality.pct | Quality % | OPS-001 |
| ops.throughput.units | Throughput (units) | OPS-001 |
| ops.downtime.pct | Downtime % | OPS-001 |
| ops.mtbf.hours | Mean time between failures | OPS-002 |
| ops.mttr.hours | Mean time to repair | OPS-002 |
| ops.downtime.unplanned.pct | Unplanned downtime % | OPS-002 |
| ops.spare_parts.stockout.pct | Spare parts stockout % | OPS-002 |
| ops.pm_compliance.pct | Preventive maintenance compliance | OPS-002 |
| quality.fpy.pct | First pass yield % | OPS-003 |
| quality.scrap.pct | Scrap % | OPS-003 |
| quality.rework.pct | Rework % | OPS-003 |
| quality.copq.amount | Cost of poor quality | OPS-003 |
| quality.complaint.pct | Complaint rate | OPS-003 |
| quality.defect_density | Defect density | OPS-003 |

---

## Supply Chain (SCM)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| inv.dio.days | Days inventory outstanding | SCM-001, FIN-001 |
| inv.turnover | Inventory turnover | SCM-001 |
| inv.stockout.pct | Stockout % | SCM-001 |
| inv.obsolete.pct | Obsolete inventory % | SCM-001 |
| supply.otif.pct | On-time in-full % | SCM-001, SCM-002, XD-003 |
| plan.forecast.accuracy.pct | Forecast accuracy | SCM-001, SCM-003 |
| supply.on_time.pct | On-time % | SCM-002 |
| supply.in_full.pct | In-full % | SCM-002 |
| supply.stockout_impact.pct | Stockout impact % | SCM-002 |
| supply.penalty.amount | Penalty amount | SCM-002 |
| supply.expedite.amount | Expedite cost | SCM-002 |
| plan.forecast.mape.pct | Forecast MAPE | SCM-003 |
| plan.forecast.bias.pct | Forecast bias | SCM-003 |
| plan.forecast.service_impact.pct | Forecast impact on service | SCM-003 |
| plan.replan.count | Replan count | SCM-003 |

---

## Experience & Service (XD)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| svc.sla.attainment.pct | SLA attainment % | XD-001, XD-002, XD-003 |
| svc.fcr.pct | First contact resolution % | XD-001 |
| svc.aht.minutes | Average handling time (min) | XD-001 |
| svc.backlog.count | Backlog count | XD-001, XD-002 |
| svc.nps.index | NPS (service context) | XD-001 |
| svc.escalation.pct | Escalation % | XD-001 |
| res.utilization.pct | Resource utilization % | XD-002 |
| res.occupancy.pct | Occupancy % | XD-002 |
| res.overtime.pct | Overtime % | XD-002 |
| res.shrinkage.pct | Shrinkage % | XD-002 |

---

## Enterprise / People (XD-003)

| KPI ID | Short purpose | Used in |
|--------|----------------|---------|
| people.digital_adoption.pct | Digital adoption % | XD-003 |
| people.attrition_risk.pct | Attrition risk % | XD-003 |
| ops.working_capital.ccc.days | Working capital CCC (executive) | XD-003 |
| ops.otif.pct | OTIF (executive view) | XD-003 |

---

## Naming Convention

- **Format:** `domain.topic.metric` (e.g. `sales.net_sales.amount`, `inv.dio.days`).
- **Domains:** sales, margin, cost, crm, fin, wc, ops, quality, inv, supply, plan, svc, res, people.
- **Source of truth:** `core/kpi_catalog/KPI_Catalog.md` and schema. This taxonomy is derived and may lag; always validate against the catalog.
