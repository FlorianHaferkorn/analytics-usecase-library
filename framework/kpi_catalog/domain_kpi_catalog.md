# Domain KPI Catalog (v1.2)

Purpose: Canonical KPI definitions used across the ActionReady Analytics Framework. Each KPI is uniquely identified by `domain.topic.metric[.type]` and must map 1:1 to a semantic-model measure and to the business/technical factsheets.

Columns: `kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage`

---

## Commercial
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| sales.net_sales.amount | Net Sales Amount | Commercial | Core revenue | Sum of net sales after discounts | € | invoice_line / month | sum | Meet/beat Plan/LY | fact_sales[Net Sales Amount] |
| sales.net_sales.delta_pct.plan | Net Sales Δ% vs Plan | Commercial | Execution vs Plan | (Net Sales − Plan) / Plan | % | month | avg | ≥ -2% guardrail | fact_sales[Net Sales Amount], fact_sales[Plan Sales Amount] |
| sales.net_sales.delta_pct.ly | Net Sales Δ% vs LY | Commercial | Growth vs LY | (Net Sales − LY) / LY | % | month | avg | ≥ +3–5% | fact_sales[Net Sales Amount], fact_sales[Last Year Sales Amount] |
| margin.gm.pct | Gross Margin % | Commercial | Profitability quality | Gross Margin / Net Sales | % | month | avg | ≥ 25% | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount] |
| margin.gm.amount | Gross Margin Amount | Commercial | Profit pool sizing | Net Sales − COGS | € | month | sum | Improve vs Plan/LY | fact_sales[Net Sales Amount], fact_sales[Cost of Goods Sold Amount] |
| margin.gm.vs_plan.pct | Gross Margin % vs Plan | Commercial | Plan comparison | (GM % − Plan GM %) / Plan GM % | pp | month | avg | ≥ 0 | GM %, plan GM % |
| sales.pvm.price_effect.amount | Price Effect Amount | Commercial | Driver | Net Sales impact from price change | € | month | sum | ≥ 0 unless price change | fact_sales[Net Price Amount], fact_sales[Plan Sales Amount], fact_sales[Quantity] |
| sales.pvm.volume_effect.amount | Volume Effect Amount | Commercial | Driver | Net Sales impact from volume change | € | month | sum | ≥ 0 unless volume change | fact_sales[Quantity], fact_sales[Plan Sales Amount] |
| sales.pvm.mix_effect.amount | Mix Effect Amount | Commercial | Driver | Net Sales impact from mix change | € | month | sum | ≥ 0 | fact_sales (PVM residual) |
| sales.price.realization_pct | Price Realization % | Commercial | Discount discipline | Net Price / List Price | % | month/promo | avg | ≥ 95% (policy) | fact_sales[Net Price Amount], fact_sales[List Price Amount] |
| sales.promo.roi.pct | Promotion ROI % | Commercial | Promo profitability | Incremental GM / Promo Cost | % | promotion | avg | ≥ 120% | fact_sales[Incremental GM], fact_promo[Promo Cost] |
| sales.promo.incremental.amount | Incremental Sales Amount | Commercial | Promo uplift sizing | Sales with promo − baseline sales | € | promotion | sum | Positive with ROI target | fact_sales[Net Sales Amount], baseline |
| sales.promo.cannibalization.pct | Cannibalization % | Commercial | Net effect on portfolio | (Sales lost in non-promoted items) / Promo uplift | % | promotion | avg | ≤ 20% | baseline vs related items |
| margin.promo.gm.pct | Promo Gross Margin % | Commercial | Profit quality in promo | GM / Net Sales during promo | % | promotion | avg | ≥ category target | fact_sales[Net Sales Amount], fact_sales[COGS], promo flag |
| cost.cogs_per_unit.amount | COGS per Unit | Commercial | Unit cost control | COGS Amount / Quantity | € | invoice_line / month | avg | Stable vs Plan/LY | fact_sales[COGS], fact_sales[Quantity] |

---

## Customer / CRM
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| crm.clv.amount | Customer Lifetime Value | Customer | Long-term profitability | PV of expected customer margin over horizon | € | customer | sum | Grow in priority segments | fact_customer_value[CLV Amount] / fact_sales grouped |
| margin.customer.amount | Customer Margin Amount | Customer | Margin pool per customer | Net Sales − COGS per customer | € | customer_month | sum | Improve vs Plan/LY | fact_sales grouped by customer |
| crm.retention.pct | Retention Rate % | Customer | Retain profitable customers | Retained customers / active prior period | % | month | avg | ≥ segment target | fact_customer_activity[Active Flag], dim_customer |
| crm.churn.pct | Churn Rate % | Customer | Control loss of customers | Churned customers / active prior period | % | month | avg | ≤ segment target | fact_customer_activity[Churn Flag], dim_customer |
| sales.customer.revenue.amount | Customer Revenue Amount | Customer | Revenue base per customer | Net Sales per customer | € | customer_month | sum | Grow with margin discipline | fact_sales[Net Sales Amount] by customer |

---

## Operations
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| ops.oee.pct | OEE % | Operations | Overall effectiveness | Availability % × Performance % × Quality % | % | line_day | avg | ≥ line target | fact_ops[Run/Planned/Output/Quality] |
| ops.availability.pct | Availability % | Operations | Uptime control | Run Time / Planned Production Time | % | line_day | avg | ≥ 90% | fact_ops[Run Time], fact_ops[Planned Time] |
| ops.performance.pct | Performance % | Operations | Speed vs standard | Actual Output / Theoretical Output | % | line_day | avg | ≥ 95% | fact_ops[Output], standards |
| ops.quality.pct | Quality % | Operations | First pass yield | Good Units / Total Units | % | line_day | avg | ≥ 98% | fact_ops[Good Units], fact_ops[Total Units] |
| ops.throughput.units | Throughput Units | Operations | Volume output | Units produced over time | qty | line_day | sum | Meet plan | fact_ops[Produced Units] |
| ops.downtime.pct | Downtime % | Operations | Loss share | Downtime / Planned Production Time | % | line_day | avg | ≤ target (e.g., <5%) | fact_ops[Downtime], fact_ops[Planned Time] |
| ops.mtbf.hours | MTBF (hours) | Operations | Reliability | Operating time between failures | hours | asset | avg | Asset target | fact_ops_failures[Failure Start/End] |
| ops.mttr.hours | MTTR (hours) | Operations | Maintainability | Average repair time per failure | hours | asset | avg | Asset target | fact_ops_failures[Repair Duration] |
| ops.downtime.unplanned.pct | Unplanned Downtime % | Operations | Unplanned loss | Unplanned downtime / Planned Time | % | asset_day | avg | ≤ target | fact_ops[Unplanned Downtime], fact_ops[Planned Time] |
| ops.spare_parts.stockout.pct | Spare Parts Stockout % | Operations | Maintenance readiness | Orders delayed due to missing parts / total orders | % | month | avg | ≤ target | fact_maintenance[Parts Stockout Flag], fact_maintenance[Orders] |
| ops.pm_compliance.pct | PM Compliance % | Operations | Preventive maintenance discipline | PM orders on time / planned PM orders | % | month | avg | ≥ 95% | fact_maintenance[PM On Time], fact_maintenance[PM Planned] |
| quality.fpy.pct | First Pass Yield % | Operations | Process quality | Good units / Total units at first pass | % | line_day | avg | ≥ line target | fact_quality[Good Units], fact_quality[Total Units] |
| quality.scrap.pct | Scrap Rate % | Operations | Waste reduction | Scrap units / Total units | % | line_day | avg | ≤ target | fact_quality[Scrap Units], fact_quality[Total Units] |
| quality.rework.pct | Rework Rate % | Operations | Rework burden | Reworked units / Total units | % | line_day | avg | ≤ target | fact_quality[Rework Units], fact_quality[Total Units] |
| quality.copq.amount | Cost of Poor Quality | Operations | Financial impact | Scrap + rework + warranty/complaint cost | € | month | sum | Reduce vs baseline | fact_quality_costs[COPQ], fact_quality |
| quality.complaint.pct | Complaint Rate % | Operations | Customer impact | Complaints / Units shipped | % | month | avg | ≤ target | fact_complaints[Complaints], fact_shipments[Units] |
| quality.defect_density | Defect Density | Operations | Defect concentration | Defects per 1k units | defects/1k | line_day | avg | ≤ target | fact_quality[Defect Count], fact_quality[Units] |

---

## Supply Chain
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| inv.dio.days | Days in Inventory (DIO) | Supply Chain | Working capital efficiency | (Avg Inventory / COGS) × Days | days | location_sku_month | avg | ≤ target | fact_inventory[Avg Inventory], fact_cogs[COGS] |
| inv.turnover | Inventory Turnover | Supply Chain | Velocity | COGS / Avg Inventory | x | location_sku_month | avg | ≥ target | fact_inventory[Avg Inventory], fact_cogs[COGS] |
| inv.stockout.pct | Stockout Rate % | Supply Chain | Service risk | Stockout occurrences / demand occurrences | % | location_sku_day | avg | ≤ target | fact_stockout[Stockout Flag], demand events |
| supply.otif.pct | OTIF % | Supply Chain | Service level | On-Time In-Full orders / total orders | % | order | avg | ≥ 97–99% | fact_fulfillment[OTIF Flag] |
| inv.obsolete.pct | Obsolete Inventory % | Supply Chain | Write-off risk | Obsolete stock / total stock | % | location_sku_month | avg | ≤ target | fact_inventory[Obsolete Stock], fact_inventory[Total Stock] |
| plan.forecast.accuracy.pct | Forecast Accuracy % | Supply Chain | Planning quality | 1 – |Forecast – Actual| / Actual | % | sku_month | avg | ≥ target | fact_forecast[Forecast], fact_sales[Actual] |
| plan.forecast.mape.pct | MAPE % | Supply Chain | Error magnitude | Mean absolute % error | % | sku_month | avg | ≤ target | fact_forecast vs fact_sales |
| plan.forecast.bias.pct | Forecast Bias % | Supply Chain | Error direction | (Forecast – Actual) / Actual | % | sku_month | avg | Near 0 band | fact_forecast vs fact_sales |
| plan.forecast.service_impact.pct | Service Impact % | Supply Chain | Service effect of forecast error | Portion of service misses attributable to forecast error | % | sku_month | avg | Minimize | linkage to OTIF/stockout |
| plan.replan.count | Re-Plan Count | Supply Chain | Planning stability | Number of re-plans within period | count | month | sum | Reduce vs baseline | planning system logs |
| supply.on_time.pct | On-Time % | Supply Chain | Timeliness | On-time deliveries / total deliveries | % | shipment | avg | ≥ 97–99% | fact_fulfillment[On-Time Flag] |
| supply.in_full.pct | In-Full % | Supply Chain | Completeness | In-full deliveries / total deliveries | % | shipment | avg | ≥ 97–99% | fact_fulfillment[In-Full Flag] |
| supply.stockout_impact.pct | Stockout Impact % | Supply Chain | Service loss | Lost demand due to stockout / total demand | % | location_sku_day | avg | ≤ target | fact_stockout[Lost Demand], fact_stockout[Demand] |
| supply.penalty.amount | Penalty Amount | Supply Chain | Cost of service failures | Penalties incurred for service misses | € | order | sum | Reduce to target | fact_fulfillment[Penalty Amount] |
| supply.expedite.amount | Expedite Cost Amount | Supply Chain | Cost to recover service | Additional cost for expedited shipping | € | shipment | sum | Reduce to target | fact_fulfillment[Expedite Cost] |

---

## Finance
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| fin.cash.balance | Cash Balance | Finance | Liquidity level | Cash and cash equivalents | € | day | sum | Meet/beat plan and buffer | fact_cash[Cash Balance] |
| fin.cash.ocf | Operating Cash Flow | Finance | Cash generation | Cash from operating activities | € | month | sum | Meet/beat plan | fact_cashflow[OCF] |
| fin.cash.vs_plan.pct | Cash vs Plan % | Finance | Performance vs plan | (Cash − Plan) / Plan | % | month | avg | ≥ 0 | fact_cash[Cash], plan_cash |
| wc.ccc.days | Cash Conversion Cycle | Finance | WC cycle | DSO + DIO − DPO | days | month | avg | Reduce to target | DSO/DIO/DPO measures |
| wc.dso.days | DSO (days) | Finance | Receivables efficiency | AR / (Revenue/365) | days | month | avg | Reduce to target | fact_ar[AR], revenue |
| wc.dio.days | DIO (days) | Finance | Inventory efficiency | Inventory / (COGS/365) | days | month | avg | Reduce to target | fact_inventory[Inventory], COGS |
| wc.dpo.days | DPO (days) | Finance | Payables efficiency | AP / (COGS/365) | days | month | avg | Optimize vs risk | fact_ap[AP], COGS |
| cost.unit.amount | Unit Cost Amount | Finance/Ops | Cost efficiency | Total COGS / Units produced or sold | €/unit | plant_line_product_month | avg | ≤ plan | fact_cost[COGS], fact_output[Units] |
| margin.cogs.pct | COGS % of Sales | Finance/Ops | Cost share | COGS / Net Sales | % | month | avg | ≤ target | fact_finance[COGS], fact_finance[Net Sales] |
| cost.opex.vs_plan.pct | OpEx vs Plan % | Finance | Overhead control | (OpEx − Plan) / Plan | % | month | avg | ≤ 0 | fact_opex[OpEx], plan_opex |
| cost.material.pct | Material Cost % | Finance/Ops | Material efficiency | Material cost / Net Sales | % | month | avg | ≤ target | fact_cost[Material Cost], fact_finance[Net Sales] |
| ops.labor.productivity.pct | Labor Productivity % | Finance/Ops | Labor efficiency | Output vs labor hours (or revenue per labor hour) | % / index | month | avg | ≥ target | fact_output[Units], fact_labor[Labor Hours] |
| profit.ebitda_margin | EBITDA Margin | Finance | Profitability | EBITDA / Net Sales | % | month | avg | ≥ target | fact_finance[EBITDA], fact_finance[Net Sales] |

---

## Service / Experience
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| svc.sla.attainment.pct | SLA Attainment % | Service | Service level compliance | Cases meeting SLA / total cases | % | day_queue | avg | ≥ target | fact_cases[SLA Met Flag] |
| svc.fcr.pct | First Contact Resolution % | Service | Quality/efficiency | Cases resolved on first contact / total cases | % | day_queue | avg | ≥ target | fact_cases[FCR Flag] |
| svc.aht.minutes | Average Handling Time (minutes) | Service | Efficiency | Avg handle time per case/contact | minutes | day_queue | avg | ≤ target band | fact_cases[Handle Time] |
| svc.backlog.count | Backlog Count | Service | Workload risk | Open cases not resolved | count | day_queue | sum | Reduce vs target | fact_cases[Backlog Flag/Open Cases] |
| svc.nps.index | NPS Index | Service | Customer satisfaction | NPS score from surveys | index | month | avg | ≥ target | fact_nps[NPS Score] |
| svc.escalation.pct | Escalation % | Service | Quality/risk | Escalated cases / total cases | % | day_queue | avg | ≤ target | fact_cases[Escalation Flag] |
| res.utilization.pct | Utilization % | Service | Productive time vs paid | (Talk/Work Time) / Paid Time | % | agent_day/queue_day | avg | Within band | fact_wfm[Work Time], fact_wfm[Paid Time] |
| res.occupancy.pct | Occupancy % | Service | Active vs available | (Talk + Wrap) / (Talk + Wrap + Idle) | % | agent_day/queue_day | avg | Within band | fact_wfm[Talk/Wrap/Idle] |
| res.overtime.pct | Overtime % | Service | Cost and fatigue | Overtime hours / Total hours | % | agent_day/region_week | avg | ≤ target | fact_wfm[Overtime Hours], fact_wfm[Total Hours] |
| res.shrinkage.pct | Shrinkage % | Service | Non-productive time | Non-productive time / Paid time | % | agent_day | avg | Within band | fact_wfm[Shrinkage], fact_wfm[Paid Time] |

---

## People / HR
| kpi_id | name | domain | purpose | definition_short | unit | grain | agg | target | lineage |
|--------|------|--------|---------|------------------|------|-------|-----|--------|---------|
| hr.turnover.pct | Employee Turnover % | HR | People stability | Leavers / Avg headcount | % | month | avg | ≤ target | fact_hr[Leavers], fact_hr[Headcount] |

