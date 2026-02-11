# Analytics Use Case Inventory

## Purpose

This document provides a **complete inventory of all implemented Use Cases** in the Analytics Framework.
Each Use Case links to standardized KPI catalogs and domain measure dictionaries.
Use Case ↔ Action Code assignments are canonical only in `core/usecases/UseCase_ActionCode_Map.yaml`.

## Commercial Cluster (COM)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Questions (summary) | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **COM-001** | Sales Performance vs Plan & LY | Explain Net Sales performance vs Plan and vs Last Year by price, volume, mix, and channel/region to protect revenue and margin. | sales.net_sales.amount, sales.net_sales.delta_pct.plan, sales.net_sales.delta_pct.ly, margin.gm.pct, sales.pvm.price_effect.amount, sales.pvm.volume_effect.amount, sales.pvm.mix_effect.amount | Where do Net Sales deviate vs Plan/LY? What is PVM contribution? Which actions close gaps fastest? | C-M2.1, C-S1.1, C-S1.2 | Faster detection of revenue gaps; targeted pricing and mix actions to stabilise gross margin; focus resources on the most material regions/channels. | Tactical | Descriptive / Diagnostic | definition_complete | build_ready |
| **COM-002** | Margin & Price Performance | Protect and improve gross margin by explaining leakage across price realization, mix, and unit cost. | margin.gm.pct, margin.gm.amount, sales.price.realization_pct, sales.pvm.mix_effect.amount, cost.cogs_per_unit.amount, margin.gm.vs_plan.pct | Where is GM eroding? What drives price/mix/cost leakage? Which actions move GM fastest? | C-M2.2, C-P4.1, C-S1.2 | +0.5-1.5 pp GM%, tighter discount discipline, clearer mix levers, faster correction of cost leakage. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |
| **COM-003** | Customer Value | Maximise customer lifetime value by improving retention, reducing churn, and prioritising profitable segments. | crm.clv.amount, crm.lifetime_revenue.amount, crm.retention.pct, crm.churned_customers.count, crm.revenue_at_risk.amount, crm.active_customers.count, crm.nps.index, crm.complaint.count | Which segments drive CLV? Where is churn rising? Which actions improve CLV and GM? | C-M2.2, C-P4.1, C-S1.2 | Higher CLV and margin through targeted retention/upsell actions; reduced revenue leakage from churn; better allocation of sales/marketing spend. | Tactical | Diagnostic / Predictive | definition_complete | build_ready |
| **COM-004** | Promotion Effectiveness | Improve promotion ROI by measuring true incremental sales and margin, controlling leakage, and optimising promo mechanics. | sales.promo.roi.pct, sales.promo.incremental.amount, margin.promo.gm.pct, sales.price.realization_pct, sales.promo.cannibalization.pct | Which promos generated incremental sales/GM? Where did discounts erode realization? What to standardize or stop? | C-M2.1, C-S1.1, C-M2.2, C-P4.1, C-S1.2 | Fewer unprofitable promos; higher incremental GM; better channel/product targeting; reduced cannibalization. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |

## Finance Cluster (FIN)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Questions (summary) | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **FIN-001** | Cash & Liquidity Performance | Control cash and liquidity by monitoring balances, operating cash flow, and working capital drivers (DSO, DIO, DPO, CCC). | fin.cash.balance, fin.cash.ocf, fin.cash.vs_plan.pct, wc.ccc.days, wc.dso.days, wc.dio.days, wc.dpo.days | What is cash vs plan? How do DSO/DIO/DPO/CCC develop? What actions improve cash quickly? | F-C1.1, F-C1.2, F-C1.3, F-C1.4 | Better liquidity visibility, reduced financing needs, faster cash conversion, and improved resilience. | Tactical | Diagnostic / Predictive | definition_complete | build_ready |
| **FIN-002** | Cost Performance | Reduce unit cost and improve margin by controlling material, labor, and OpEx vs plan. | cost.unit.amount, margin.cogs.pct, cost.opex.vs_plan.pct, cost.material.pct, ops.labor.productivity.pct | What is unit cost vs plan? Which cost buckets drive variance? Which actions reduce cost without harming service? | F-K2.1, F-K2.2, F-K2.3, F-K2.4 | Better cost competitiveness, margin protection, and more efficient operations without sacrificing throughput/quality. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |

## Operations Cluster (OPS)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Questions (summary) | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **OPS-001** | Operations Performance | Improve overall equipment effectiveness and throughput by addressing availability, performance, and quality losses. | ops.oee.pct, ops.availability.pct, ops.performance.pct, ops.quality.pct, ops.throughput.units, ops.downtime.pct | What is OEE by line/plant? Where are the largest downtime/speed losses? Which actions lift OEE fastest? | O-O1.1, O-O1.2, O-O1.3, O-O1.4 | Higher OEE, more stable throughput, reduced downtime, and better cost efficiency without additional CAPEX. | Tactical / Operational | Diagnostic | definition_complete | build_ready |
| **OPS-002** | Asset Performance | Improve asset reliability and availability by reducing unplanned downtime and optimizing preventive maintenance. | ops.availability.pct, ops.mtbf.hours, ops.mttr.hours, ops.downtime.unplanned.pct, ops.spare_parts.stockout.pct, ops.pm_compliance.pct | Which assets have highest unplanned downtime? How do MTBF/MTTR trend? Which actions reduce downtime fastest? | O-A2.1, O-A2.2, O-A2.3, O-A2.4, O-A2.5 | Higher availability, fewer breakdowns, lower maintenance cost from better PM compliance and spare-part readiness. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |
| **OPS-003** | Quality & Yield | Improve first pass yield and reduce scrap/rework by identifying top defect drivers and cost of poor quality. | quality.fpy.pct, quality.scrap.pct, quality.rework.pct, quality.copq.amount, quality.complaint.pct, quality.defect_density | What is FPY/scrap/rework by line/product? Which defect types drive COPQ? Which actions reduce defects fastest? | O-Q3.1, O-Q3.2, O-Q3.3, O-Q3.4, O-Q3.5 | Higher yield, lower scrap/rework cost, fewer customer complaints, more stable throughput and margin. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | build_ready |

## Supply Chain Cluster (SCM)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Questions (summary) | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **SCM-001** | Inventory Performance | Optimize inventory by balancing availability (service level) and working capital, reducing excess, stockouts, and obsolescence. | inv.dio.days, inv.turnover, inv.stockout.pct, supply.otif.pct, inv.obsolete.pct, plan.forecast.accuracy.pct | Where are DIO/turnover off target? Which items drive stockouts? Which actions reduce inventory without hurting service? | S-I1.1, S-I1.2, S-I1.3, S-I1.4, S-I1.5 | Lower working capital, fewer stockouts, higher OTIF, and reduced write-offs. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |
| **SCM-002** | Supply Reliability & OTIF | Improve supply reliability by raising On-Time In-Full (OTIF), reducing stockout impact, and lowering penalties/expedites. | supply.otif.pct, supply.on_time.pct, supply.in_full.pct, supply.stockout_impact.pct, supply.penalty.amount, supply.expedite.amount | Where is OTIF below target? What drives late/incomplete deliveries? Which actions improve OTIF fastest? | S-R2.1, S-R2.2, S-R2.3, S-R2.4, S-R2.5 | Higher service level, fewer penalties/expedites, better customer satisfaction, and more stable inventory. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |
| **SCM-003** | Forecast vs Actual | Improve forecast accuracy and bias to stabilize supply, service level, and inventory. | plan.forecast.accuracy.pct, plan.forecast.mape.pct, plan.forecast.bias.pct, plan.forecast.service_impact.pct, plan.replan.count | Where is forecast accuracy/bias below target? Which products drive errors? Which actions improve forecast quality? | S-F3.1, S-F3.2, S-F3.3, S-F3.4 | Fewer re-plans, better OTIF/stockout performance, lower working capital driven by better forecast quality. | Tactical | Diagnostic / Prescriptive | definition_complete | build_ready |

## Experience Cluster (XD)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Questions (summary) | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **XD-001** | Service Level Performance | Improve service level by monitoring SLA attainment, first contact resolution, handling time, backlog, and escalation. | svc.sla.attainment.pct, svc.fcr.pct, svc.aht.minutes, svc.backlog.count, svc.nps.index, svc.escalation.pct | Where is SLA below target? How do FCR/AHT affect SLA and NPS? Which actions improve service level fastest? | X-S1.1, X-S1.2, X-S1.3, X-S1.4 | Higher customer satisfaction, lower cost-to-serve, reduced escalations and backlog. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | build_ready |
| **XD-002** | Resource Utilization | Optimize resource utilization and occupancy while protecting SLA and customer experience. | res.utilization.pct, res.occupancy.pct, svc.sla.attainment.pct, res.overtime.pct, res.shrinkage.pct, svc.backlog.count | What are utilization/occupancy vs targets? Where do staffing imbalances create SLA risk? Which actions improve utilization? | X-R2.1, X-R2.2, X-R2.3, X-R2.4 | Better staffing efficiency, reduced overtime/shrinkage costs, and controlled backlog without SLA degradation. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | build_ready |
| **XD-003** | Executive KPI Overview | Provide a unified, enterprise-wide performance cockpit for leadership. | sales.net_sales.delta_pct.ly, margin.gm.pct, crm.clv.amount, svc.sla.attainment.pct, ops.otif.pct, ops.working_capital.ccc.days, people.digital_adoption.pct, people.attrition_risk.pct | Are we growing profitably? Is margin healthy? Is supply chain reliable? Are we efficient on working capital and people? | X-E3.2, X-E3.3 | Aggregates critical financial, customer, operational, and people KPIs into one strategic view to assess if the company is on track and to surface cross-domain interventions rapidly via the 3-30-300 navigation. | Strategic | Descriptive / Diagnostic | definition_complete | build_ready |

## Key Questions by Use Case (Full List)

Key questions bridge Strategic KPIs to decisions; they are the analytical intent of each use case. Full sets are in each use case's Business Factsheet (section 2. Core Business Questions).

| Use Case | Key Questions |
|----------|---------------|
| COM-001 | Where do Net Sales deviate most vs Plan and vs LY by region, channel, product? What is the contribution of price, volume, and mix to the gap? Which segments drive negative GM %? Which actions close the largest gaps fastest? How persistent are the gaps? |
| COM-002 | Where is gross margin eroding vs Plan and vs LY? Which products/channels/regions drive negative price realization or adverse mix? How do discounts, rebates, surcharges affect realized price? Which cost components dilute margin? Which actions move GM fastest? |
| COM-003 | Which customers/segments drive the highest and lowest CLV and margin? Where is churn rising and what are leading indicators? Which actions (retention, upsell, pricing) improve CLV and GM? How concentrated is revenue/margin? Which products/channels deliver best CLV uplift? |
| COM-004 | Which promotions generated true incremental sales and GM? Which channels/products deliver highest promo ROI? How much did discounts erode price realization and GM? What promo depth/timing/mechanics to standardize or stop? Where do cannibalization or leakage offset uplift? |
| FIN-001 | What is cash position vs plan and how is OCF trending? How do DSO, DIO, DPO, CCC develop by region/entity? Which customers/suppliers drive cash conversion issues? What actions improve cash quickly with minimal business risk? |
| FIN-002 | What is unit cost vs plan/LY by plant/line/product? Which cost buckets (material, labor, OpEx) drive variance? Where is COGS % rising and margin eroding? Which actions reduce cost fastest without harming service/quality? |
| OPS-001 | What is OEE and its components (availability, performance, quality) by line/plant? Where are the largest downtime and speed losses, and top causes? How does throughput vary by shift, line, product mix? Which targeted actions lift OEE fastest? |
| OPS-002 | Which assets/lines have highest unplanned downtime and root causes? How do MTBF/MTTR trend by asset class and site? Is preventive maintenance on time and effective? Where do spare-part stockouts create risk? Which actions reduce downtime fastest? |
| OPS-003 | What is FPY and scrap/rework performance by line, product, shift? Which defect types and steps drive most quality losses and COPQ? How do complaints correlate with plant/line/product? Which actions reduce defects fastest with minimal throughput impact? |
| SCM-001 | Where are inventory days and turnover off target by location/channel/category? Which items drive stockouts and OTIF misses? Where is excess/obsolete inventory accumulating? Which actions reduce inventory without hurting service? How does forecast accuracy impact inventory KPIs? |
| SCM-002 | Where is OTIF below target by lane/DC/channel/product? What are main drivers of late or incomplete deliveries? How much do stockouts, penalties, expedites cost? Which corrective actions improve OTIF fastest without excessive cost? |
| SCM-003 | Where is forecast accuracy and bias below target by channel/category/location? Which products drive largest forecast errors and service impact? How often are re-plans triggered and why? Which actions (process, data, parameters) improve forecast quality fastest? |
| XD-001 | Where is SLA attainment below target by channel/region/queue? How do FCR and AHT trend, and how do they affect SLA and NPS? Which queues/regions drive backlog and escalations? Which actions improve service level fastest without quality loss? |
| XD-002 | What are utilization and occupancy by channel/queue/region vs targets? How do overtime and shrinkage affect SLA attainment and backlog? Where do staffing imbalances create SLA risk or idle capacity? Which actions improve utilization without harming quality? |
| XD-003 | Are we growing profitably and in line with the strategic plan? Is margin performance healthy across price, mix, and cost? Are we delivering expected value to customers? Is supply chain reliable and stable? Are we operating with sufficient working capital efficiency? Are digital tools adopted and are we retaining key talent? |

---

## Summary Overview

| Cluster | Use Cases |
|---------|-----------|
| Commercial Cluster (COM) | 4 |
| Finance Cluster (FIN) | 2 |
| Operations Cluster (OPS) | 3 |
| Supply Chain Cluster (SCM) | 3 |
| Experience Cluster (XD) | 3 |
| **Total** | **15** |

## Governance & Review Summary

| Metric | Value |
|--------|--------|
| **Total Strategic KPIs Supported** | TBD |
| **Total Use Cases** | 15 |
| **Copilot Ready** | Yes |
| **Review Frequency** | Quarterly |
| **Maintainers** | analytics-core-team |
| **Contact** | <analytics-governance@company.com> |

