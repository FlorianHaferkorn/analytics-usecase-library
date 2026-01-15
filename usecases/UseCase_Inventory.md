# Analytics Use Case Inventory

---

## Purpose

This document provides a **complete inventory of all implemented Use Cases** in the Analytics Framework.
Each Use Case links to standardized KPI catalogs and domain measure dictionaries.

---

## Commercial Cluster (COM)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Drivers | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **COM-001** | Sales Performance vs Plan & LY | Explain Net Sales performance vs Plan and vs Last Year by price, volume, mix, and channel/region to protect revenue and margin. | sales.net_sales.amount, sales.net_sales.delta_pct.plan, sales.net_sales.delta_pct.ly, margin.gm.pct, sales.pvm.price_effect.amount, sales.pvm.volume_effect.amount, sales.pvm.mix_effect.amount | TBD | P2, P4, M3, D1 | Faster detection of revenue gaps; targeted pricing and mix actions to stabilise gross margin; focus resources on the most material regions/channels. | Tactical | Descriptive / Diagnostic | definition_complete | in_review |
| **COM-002** | Margin & Price Performance | Protect and improve gross margin by explaining leakage across price realization, mix, and unit cost. | margin.gm.pct, margin.gm.amount, sales.price.realization_pct, sales.pvm.mix_effect.amount, cost.cogs_per_unit.amount, margin.gm.vs_plan.pct | TBD | P2, M3, D1, PC2 | +0.5-1.5 pp GM%, tighter discount discipline, clearer mix levers, faster correction of cost leakage. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |
| **COM-003** | Customer Value | Maximise customer lifetime value by improving retention, reducing churn, and prioritising profitable segments. | crm.clv.amount, crm.lifetime_revenue.amount, crm.retention.pct, crm.churned_customers.count, crm.revenue_at_risk.amount, crm.active_customers.count, crm.nps.index, crm.complaint.count | TBD | C1, P2, M3, D1 | Higher CLV and margin through targeted retention/upsell actions; reduced revenue leakage from churn; better allocation of sales/marketing spend. | Tactical | Diagnostic / Predictive | definition_complete | in_review |
| **COM-004** | Promotion Effectiveness | Improve promotion ROI by measuring true incremental sales and margin, controlling leakage, and optimising promo mechanics. | sales.promo.roi.pct, sales.promo.incremental.amount, margin.promo.gm.pct, sales.price.realization_pct, sales.promo.cannibalization.pct | TBD | PC2, P2, M3, D1 | Fewer unprofitable promos; higher incremental GM; better channel/product targeting; reduced cannibalization. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |

---

## Finance Cluster (FIN)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Drivers | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **FIN-001** | Cash & Liquidity Performance | Control cash and liquidity by monitoring balances, operating cash flow, and working capital drivers (DSO, DIO, DPO, CCC). | fin.cash.balance, fin.cash.ocf, fin.cash.vs_plan.pct, wc.ccc.days, wc.dso.days, wc.dio.days, wc.dpo.days | TBD | W1, C1, I1, W2 | Better liquidity visibility, reduced financing needs, faster cash conversion, and improved resilience. | Tactical | Diagnostic / Predictive | definition_complete | in_review |
| **FIN-002** | Cost Performance | Reduce unit cost and improve margin by controlling material, labor, and OpEx vs plan. | cost.unit.amount, margin.cogs.pct, cost.opex.vs_plan.pct, cost.material.pct, ops.labor.productivity.pct | TBD | D1, PC2, M2, W1 | Better cost competitiveness, margin protection, and more efficient operations without sacrificing throughput/quality. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |

---

## Operations Cluster (OPS)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Drivers | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **OPS-001** | Operations Performance | Improve overall equipment effectiveness and throughput by addressing availability, performance, and quality losses. | ops.oee.pct, ops.availability.pct, ops.performance.pct, ops.quality.pct, ops.throughput.units, ops.downtime.pct | TBD | O2, M2, L2, D1 | Higher OEE, more stable throughput, reduced downtime, and better cost efficiency without additional CAPEX. | Tactical / Operational | Diagnostic | definition_complete | in_review |
| **OPS-002** | Asset Performance | Improve asset reliability and availability by reducing unplanned downtime and optimizing preventive maintenance. | ops.availability.pct, ops.mtbf.hours, ops.mttr.hours, ops.downtime.unplanned.pct, ops.spare_parts.stockout.pct, ops.pm_compliance.pct | TBD | O2, L2, D1, M2 | Higher availability, fewer breakdowns, lower maintenance cost from better PM compliance and spare-part readiness. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |
| **OPS-003** | Quality & Yield | Improve first pass yield and reduce scrap/rework by identifying top defect drivers and cost of poor quality. | quality.fpy.pct, quality.scrap.pct, quality.rework.pct, quality.copq.amount, quality.complaint.pct, quality.defect_density | TBD | L2, O2, D1, M2 | Higher yield, lower scrap/rework cost, fewer customer complaints, more stable throughput and margin. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | in_review |

---

## Supply Chain Cluster (SCM)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Drivers | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **SCM-001** | Inventory Performance | Optimize inventory by balancing availability (service level) and working capital, reducing excess, stockouts, and obsolescence. | inv.dio.days, inv.turnover, inv.stockout.pct, supply.otif.pct, inv.obsolete.pct, plan.forecast.accuracy.pct | TBD | I1, I2, D1, O2 | Lower working capital, fewer stockouts, higher OTIF, and reduced write-offs. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |
| **SCM-002** | Supply Reliability & OTIF | Improve supply reliability by raising On-Time In-Full (OTIF), reducing stockout impact, and lowering penalties/expedites. | supply.otif.pct, supply.on_time.pct, supply.in_full.pct, supply.stockout_impact.pct, supply.penalty.amount, supply.expedite.amount | TBD | O2, I2, D1 | Higher service level, fewer penalties/expedites, better customer satisfaction, and more stable inventory. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |
| **SCM-003** | Forecast vs Actual | Improve forecast accuracy and bias to stabilize supply, service level, and inventory. | plan.forecast.accuracy.pct, plan.forecast.mape.pct, plan.forecast.bias.pct, plan.forecast.service_impact.pct, plan.replan.count | TBD | O2, I2, D1 | Fewer re-plans, better OTIF/stockout performance, lower working capital driven by better forecast quality. | Tactical | Diagnostic / Prescriptive | definition_complete | in_review |

---

## Experience Cluster (XD)

| ID | Use Case Title | Purpose / Goal | Strategic KPIs | Key Drivers | Main Action Codes | Expected Impact | Reporting Level | Analytics Stage | Maturity | Status |
|----|----------------|----------------|----------------|-------------|-------------------|-----------------|-----------------|-----------------|----------|--------|
| **XD-001** | Service Level Performance | Improve service level by monitoring SLA attainment, first contact resolution, handling time, backlog, and escalation. | svc.sla.attainment.pct, svc.fcr.pct, svc.aht.minutes, svc.backlog.count, svc.nps.index, svc.escalation.pct | TBD | O2, L2, M2, D1 | Higher customer satisfaction, lower cost-to-serve, reduced escalations and backlog. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | in_review |
| **XD-002** | Resource Utilization | Optimize resource utilization and occupancy while protecting SLA and customer experience. | res.utilization.pct, res.occupancy.pct, svc.sla.attainment.pct, res.overtime.pct, res.shrinkage.pct, svc.backlog.count | TBD | O2, M2, L2, D1 | Better staffing efficiency, reduced overtime/shrinkage costs, and controlled backlog without SLA degradation. | Tactical / Operational | Diagnostic / Prescriptive | definition_complete | in_review |
| **XD-003** | Executive KPI Overview | Provide a unified, enterprise-wide performance cockpit for leadership. | sales.net_sales.delta_pct.ly, margin.gm.pct, crm.clv.amount, svc.sla.attainment.pct, ops.otif.pct, ops.working_capital.ccc.days, people.digital_adoption.pct, people.attrition_risk.pct | TBD | P2, P4, C2, S3, F1, H1 | Aggregates critical financial, customer, operational, and people KPIs into one strategic view to assess if the company is on track and to surface cross-domain interventions rapidly via the 3-30-300 navigation. | Strategic | Descriptive / Diagnostic | definition_complete | in_review |

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

---

## Governance & Review Summary

| Metric | Value |
|--------|--------|
| **Total Strategic KPIs Supported** | TBD |
| **Total Use Cases** | 15 |
| **Copilot Ready** | Yes |
| **Review Frequency** | Quarterly |
| **Maintainers** | analytics-core-team |
| **Contact** | <analytics-governance@company.com> |
