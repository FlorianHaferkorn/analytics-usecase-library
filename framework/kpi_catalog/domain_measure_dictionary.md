# Domain Measure Dictionary (v1.2)

Purpose: Canonical mapping of KPIs to semantic model measures, including display folder and format. Use these definitions to keep Business/Technical Factsheets, semantic models, and data contracts aligned.

Columns: `kpi_id | measure_name | domain | folder | format | notes`

---

## Commercial
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| sales.net_sales.amount | [Net Sales Amount] | Commercial | 01_Revenue | €#,0 | KPI |
| sales.net_sales.delta_pct.plan | [Net Sales % vs Plan] | Commercial | 01_Revenue | 0.0% | KPI |
| sales.net_sales.delta_pct.ly | [Net Sales % vs LY] | Commercial | 01_Revenue | 0.0% | KPI |
| margin.gm.pct | [Gross Margin %] | Commercial | 02_Margin | 0.0% | KPI |
| margin.gm.amount | [Gross Margin Amount] | Commercial | 02_Margin | €#,0 | KPI |
| margin.gm.vs_plan.pct | [Gross Margin % vs Plan] | Commercial | 02_Margin | 0.0 pp | KPI |
| sales.pvm.price_effect.amount | [Price Effect Amount] | Commercial | 03_PVM | €#,0 | Driver |
| sales.pvm.volume_effect.amount | [Volume Effect Amount] | Commercial | 03_PVM | €#,0 | Driver |
| sales.pvm.mix_effect.amount | [Mix Effect Amount] | Commercial | 03_PVM | €#,0 | Driver |
| sales.price.realization_pct | [Price Realization %] | Commercial | 03_Pricing | 0.0% | KPI |
| sales.promo.roi.pct | [Promotion ROI %] | Commercial | 04_Promo | 0.0% | KPI |
| sales.promo.incremental.amount | [Incremental Sales Amount] | Commercial | 04_Promo | €#,0 | KPI |
| sales.promo.cannibalization.pct | [Cannibalization %] | Commercial | 04_Promo | 0.0% | KPI |
| margin.promo.gm.pct | [Promo Gross Margin %] | Commercial | 02_Margin | 0.0% | KPI |
| cost.cogs_per_unit.amount | [COGS per Unit] | Commercial | 02_Margin | €#,0.00 | KPI |

## Customer / CRM
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| crm.clv.amount | [Customer Lifetime Value] | Customer | 04_Customer | €#,0 | KPI |
| margin.customer.amount | [Customer Margin Amount] | Customer | 02_Margin | €#,0 | KPI |
| crm.retention.pct | [Retention %] | Customer | 04_Customer | 0.0% | KPI |
| crm.churn.pct | [Churn %] | Customer | 04_Customer | 0.0% | KPI |
| sales.customer.revenue.amount | [Customer Revenue Amount] | Customer | 01_Revenue | €#,0 | KPI |

## Operations
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| ops.oee.pct | [OEE %] | Operations | 05_Ops | 0.0% | KPI |
| ops.availability.pct | [Availability %] | Operations | 05_Ops | 0.0% | KPI |
| ops.performance.pct | [Performance %] | Operations | 05_Ops | 0.0% | KPI |
| ops.quality.pct | [Quality %] | Operations | 05_Ops | 0.0% | KPI |
| ops.throughput.units | [Throughput Units] | Operations | 01_Output | #,0 | KPI |
| ops.downtime.pct | [Downtime %] | Operations | 05_Ops | 0.0% | KPI |
| ops.mtbf.hours | [MTBF (hours)] | Operations | 05_Ops | #,0.0 | KPI |
| ops.mttr.hours | [MTTR (hours)] | Operations | 05_Ops | #,0.0 | KPI |
| ops.downtime.unplanned.pct | [Unplanned Downtime %] | Operations | 05_Ops | 0.0% | KPI |
| ops.spare_parts.stockout.pct | [Spare Parts Stockout %] | Operations | 06_Maintenance | 0.0% | KPI |
| ops.pm_compliance.pct | [PM Compliance %] | Operations | 06_Maintenance | 0.0% | KPI |
| quality.fpy.pct | [First Pass Yield %] | Operations | 07_Quality | 0.0% | KPI |
| quality.scrap.pct | [Scrap Rate %] | Operations | 07_Quality | 0.0% | KPI |
| quality.rework.pct | [Rework Rate %] | Operations | 07_Quality | 0.0% | KPI |
| quality.copq.amount | [Cost of Poor Quality] | Operations | 07_Quality | €#,0 | KPI |
| quality.complaint.pct | [Complaint Rate %] | Operations | 07_Quality | 0.0% | KPI |
| quality.defect_density | [Defect Density] | Operations | 07_Quality | #,0.00 | KPI |

## Supply Chain
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| inv.dio.days | [Days in Inventory] | SCM | 08_SCM_Inventory | #,0.0 | KPI |
| inv.turnover | [Inventory Turnover] | SCM | 08_SCM_Inventory | #,0.0 | KPI |
| inv.stockout.pct | [Stockout Rate %] | SCM | 08_SCM_Service | 0.0% | KPI |
| supply.otif.pct | [OTIF %] | SCM | 08_SCM_Service | 0.0% | KPI |
| inv.obsolete.pct | [Obsolete Inventory %] | SCM | 08_SCM_Inventory | 0.0% | KPI |
| plan.forecast.accuracy.pct | [Forecast Accuracy %] | SCM | 09_Planning | 0.0% | KPI |
| plan.forecast.mape.pct | [MAPE %] | SCM | 09_Planning | 0.0% | KPI |
| plan.forecast.bias.pct | [Bias %] | SCM | 09_Planning | 0.0% | KPI |
| plan.forecast.service_impact.pct | [Service Impact %] | SCM | 08_SCM_Service | 0.0% | KPI |
| plan.replan.count | [Re-Plan Count] | SCM | 09_Planning | #,0 | KPI |
| supply.on_time.pct | [On-Time %] | SCM | 08_SCM_Service | 0.0% | KPI |
| supply.in_full.pct | [In-Full %] | SCM | 08_SCM_Service | 0.0% | KPI |
| supply.stockout_impact.pct | [Stockout Impact %] | SCM | 08_SCM_Service | 0.0% | KPI |
| supply.penalty.amount | [Penalty Amount] | SCM | 08_SCM_Cost | €#,0 | KPI |
| supply.expedite.amount | [Expedite Cost Amount] | SCM | 08_SCM_Cost | €#,0 | KPI |

## Finance
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| fin.cash.balance | [Cash Balance] | Finance | 10_Finance | €#,0 | KPI |
| fin.cash.ocf | [Operating Cash Flow] | Finance | 10_Finance | €#,0 | KPI |
| fin.cash.vs_plan.pct | [Cash vs Plan %] | Finance | 10_Finance | 0.0% | KPI |
| wc.ccc.days | [CCC Days] | Finance | 10_Finance | #,0.0 | KPI |
| wc.dso.days | [DSO Days] | Finance | 10_Finance | #,0.0 | KPI |
| wc.dio.days | [DIO Days] | Finance | 10_Finance | #,0.0 | KPI |
| wc.dpo.days | [DPO Days] | Finance | 10_Finance | #,0.0 | KPI |
| cost.unit.amount | [Unit Cost Amount] | Finance/Ops | 10_Finance | €#,0.00 | KPI |
| margin.cogs.pct | [COGS % of Sales] | Finance/Ops | 10_Finance | 0.0% | KPI |
| cost.opex.vs_plan.pct | [OpEx vs Plan %] | Finance | 10_Finance | 0.0% | KPI |
| cost.material.pct | [Material Cost %] | Finance/Ops | 10_Finance | 0.0% | KPI |
| ops.labor.productivity.pct | [Labor Productivity %] | Finance/Ops | 05_Ops | 0.0% | KPI |
| profit.ebitda_margin | [EBITDA Margin] | Finance | 10_Finance | 0.0% | KPI |

## Service / Experience
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| svc.sla.attainment.pct | [SLA Attainment %] | Service | 11_Service | 0.0% | KPI |
| svc.fcr.pct | [FCR %] | Service | 11_Service | 0.0% | KPI |
| svc.aht.minutes | [AHT Minutes] | Service | 11_Service | 0.0 | KPI |
| svc.backlog.count | [Backlog Count] | Service | 11_Service | #,0 | KPI |
| svc.nps.index | [NPS Index] | Service | 11_Service | #,0 | KPI |
| svc.escalation.pct | [Escalation %] | Service | 11_Service | 0.0% | KPI |
| res.utilization.pct | [Utilization %] | Service | 11_Service | 0.0% | KPI |
| res.occupancy.pct | [Occupancy %] | Service | 11_Service | 0.0% | KPI |
| res.overtime.pct | [Overtime %] | Service | 11_Service | 0.0% | KPI |
| res.shrinkage.pct | [Shrinkage %] | Service | 11_Service | 0.0% | KPI |

## People / HR
| kpi_id | measure_name | domain | folder | format | notes |
|--------|--------------|--------|--------|--------|-------|
| hr.turnover.pct | [Employee Turnover %] | HR | 05_People | 0.0% | KPI |

---

Notes:
- Formats follow measure_system.md conventions (currency with €#,0 or €#,0.00; % with one decimal where applicable).
- Folder names align with semantic model patterns used in Technical Factsheets.
- If a KPI requires supporting measures (e.g., denominators), define them in the domain semantic model with the same folder and clear naming. TODO markers should be added in the domain dictionaries if any supporting measure is missing in implementation.
