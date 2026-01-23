# KPI Catalog - Efficiency

---

Schema: see `/_includes/kpi_catalog/KPI_Catalog_SCHEMA.md`

## KPIs - Strategic

```yaml
- kpi_id: ops.performance.pct
  kpi_key: Performance %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Throughput speed versus theoretical maximum.
    definition: Actual output / Theoretical maximum output
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher performance indicates faster throughput; values above 100 % require validation of standard rates.
  technical:
    dax_name: Performance %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Production Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Performance % bounded between 0 % and 150 %; investigate values outside expected range by line.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025








- kpi_id: ops.quality.pct
  kpi_key: Quality %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Yield of conforming units relative to total units produced.
    definition: Good units / Total units
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher quality means fewer defects; low values indicate scrap/rework issues.
  technical:
    dax_name: Quality %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Quality Engineer
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Quality % bounded between 0 % and 100 %; reconcile to scrap/rework reporting within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.labor.productivity.pct
  kpi_key: Labor Productivity %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: rate
  business:
    purpose: Shows output efficiency relative to labor input.
    definition: Output Units or Net Sales divided by Labor Hours (normalized to % baseline).
    grain_scope: Line/site; reported weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better labor efficiency; validate against mix effects.
  technical:
    dax_name: Labor Productivity %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Labor Hours > 0
    - Outliers reviewed for mix/shift effects
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.mtbf.hours
  kpi_key: MTBF (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: amount
  business:
    purpose: Measures average operating time between failures.
    definition: Operating Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours
    interpretation: Higher is better; declining MTBF indicates reliability issues.
  technical:
    dax_name: MTBF (hours)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Reliability Engineer
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures count > 0 for ratio
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.mttr.hours
  kpi_key: MTTR (hours)
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: amount
  business:
    purpose: Measures average repair time after failures.
    definition: Total Repair Time Hours / Number of Failures.
    grain_scope: Asset/line; aggregated monthly.
    unit_format: hours
    interpretation: Lower is better; high MTTR indicates slow recovery or parts issues.
  technical:
    dax_name: MTTR (hours)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Lead
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures count > 0 for ratio
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.pm_compliance.pct
  kpi_key: PM Compliance %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: rate
  business:
    purpose: Tracks adherence to preventive maintenance plan.
    definition: Completed PM Orders / Planned PM Orders.
    grain_scope: Site/asset; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low compliance increases breakdown risk.
  technical:
    dax_name: PM Compliance %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Maintenance
    data_owner: Operations BI
    steward: Maintenance Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned PM Orders > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.spare_parts.stockout.pct
  kpi_key: Spare Parts Stockout %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: rate
  business:
    purpose: Measures stockout frequency for critical spare parts.
    definition: Stockout Events / Total Parts Requests.
    grain_scope: Site/part; monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; stockouts drive downtime and MTTR.
  technical:
    dax_name: Spare Parts Stockout %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Maintenance
    data_owner: Operations BI
    steward: Spare Parts Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Requests count > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.throughput.units
  kpi_key: Throughput Units
  kpi_type: quantity
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: count
  business:
    purpose: Measures total output volume in units.
    definition: Sum of produced units in the period.
    grain_scope: Line/day; aggregated to site and month.
    unit_format: units
    interpretation: Higher values indicate higher output; analyze against capacity and demand.
  technical:
    dax_name: Throughput Units
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Output Units >= 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: quality.fpy.pct
  kpi_key: First Pass Yield %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: rate
  business:
    purpose: Measures share of units produced without rework or scrap.
    definition: Good Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low FPY indicates process instability.
  technical:
    dax_name: First Pass Yield %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: quality.scrap.pct
  kpi_key: Scrap Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: rate
  business:
    purpose: Measures share of units scrapped in production.
    definition: Scrap Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; rising scrap increases cost and reduces yield.
  technical:
    dax_name: Scrap Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: quality.rework.pct
  kpi_key: Rework Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: rate
  business:
    purpose: Measures share of units requiring rework.
    definition: Reworked Units / Total Units.
    grain_scope: Line/day; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high rework impacts throughput and cost.
  technical:
    dax_name: Rework Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: quality.copq.amount
  kpi_key: Cost of Poor Quality
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: amount
  business:
    purpose: Captures financial impact of scrap, rework, and warranty/complaints.
    definition: Sum of cost impacts for quality failures in period.
    grain_scope: Site/month; aggregated to business unit.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high COPQ indicates process and supplier issues.
  technical:
    dax_name: Cost of Poor Quality
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Reconciles to quality cost ledger within +/-2 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: quality.complaint.pct
  kpi_key: Complaint Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: rate
  business:
    purpose: Measures customer complaints relative to shipped units.
    definition: Complaint Count / Units Shipped.
    grain_scope: Product/month; aggregated to business unit.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; spikes indicate quality or service issues.
  technical:
    dax_name: Complaint Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Units Shipped > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - crm.complaint.rate.pct

- kpi_id: quality.defect_density
  kpi_key: Defect Density
  kpi_type: rate
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-003
  calc_type: rate
  business:
    purpose: Measures defect count per 1,000 units produced.
    definition: (Defect Count / Total Units) * 1,000.
    grain_scope: Line/day; aggregated monthly.
    unit_format: defects per 1k units
    interpretation: Lower is better; indicates process stability.
  technical:
    dax_name: Defect Density
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Operations BI
    steward: Quality Manager
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Units > 0
    - Defect Count >= 0
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: inv.dio.days
  kpi_key: Days in Inventory
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  calc_type: amount
  business:
    purpose: Measures inventory holding period in days.
    definition: Average Inventory / (COGS / 365).
    grain_scope: SKU/location; aggregated monthly.
    unit_format: days
    interpretation: Higher values indicate slower movement and more cash tied up.
  technical:
    dax_name: Days in Inventory
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory and COGS reconciled to ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: inv.stockout.pct
  kpi_key: Stockout Rate %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  calc_type: rate
  business:
    purpose: Measures how often inventory is unavailable when demanded.
    definition: Stockout Events / Total Demand Events.
    grain_scope: SKU/location; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high stockout rate impacts service and revenue.
  technical:
    dax_name: Stockout Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Demand Events > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: inv.obsolete.pct
  kpi_key: Obsolete Inventory %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  calc_type: rate
  business:
    purpose: Measures share of inventory considered obsolete.
    definition: Obsolete Inventory Value / Total Inventory Value.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high obsolescence indicates slow movement or aging.
  technical:
    dax_name: Obsolete Inventory %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Value between 0 % and 100 %
    - Obsolete definition documented
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: plan.forecast.accuracy.pct
  kpi_key: Forecast Accuracy %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  calc_type: rate
  business:
    purpose: Measures how close forecasted demand is to actual demand.
    definition: 1 - |Forecast - Actual| / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low accuracy drives inventory and service issues.
  technical:
    dax_name: Forecast Accuracy %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: plan.forecast.bias.pct
  kpi_key: Forecast Bias %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  calc_type: rate
  business:
    purpose: Measures systematic over- or under-forecasting.
    definition: (Forecast - Actual) / Actual.
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Values near 0 are best; positive bias indicates over-forecasting.
  technical:
    dax_name: Forecast Bias %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Bias bounded and reviewed for outliers
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - sales.forecast.bias_pct

- kpi_id: plan.replan.count
  kpi_key: Re-Plan Count
  kpi_type: activity
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  calc_type: count
  business:
    purpose: Counts number of replanning cycles in a period.
    definition: Total replan events logged in planning system.
    grain_scope: Planning cycle; aggregated monthly.
    unit_format: count
    interpretation: High values indicate planning instability or frequent disruptions.
  technical:
    dax_name: Re-Plan Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Replan events counted once per cycle
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.otif.pct
  kpi_key: OTIF %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: rate
  business:
    purpose: Measures share of orders delivered on time and in full.
    definition: OTIF Orders / Total Orders.
    grain_scope: Order/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; key service level indicator.
  technical:
    dax_name: OTIF %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Orders > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.on_time.pct
  kpi_key: On-Time %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: rate
  business:
    purpose: Measures share of deliveries arriving on time.
    definition: On-Time Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; analyze by carrier and lane.
  technical:
    dax_name: On-Time %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Deliveries > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.stockout_impact.pct
  kpi_key: Stockout Impact %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: rate
  business:
    purpose: Measures lost demand share due to stockouts.
    definition: Lost Demand Qty / Total Demand Qty.
    grain_scope: SKU/location/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; ties inventory and service performance.
  technical:
    dax_name: Stockout Impact %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Demand Qty > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.expedite.amount
  kpi_key: Expedite Cost Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: amount
  business:
    purpose: Captures additional cost for expedited shipments.
    definition: Sum of expedite fees and premium freight charges.
    grain_scope: Shipment/month.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high values indicate planning or supply issues.
  technical:
    dax_name: Expedite Cost Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Expedite costs reconciled to logistics ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.penalty.amount
  kpi_key: Penalty Amount
  kpi_type: amount
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: amount
  business:
    purpose: Captures penalties for service level breaches.
    definition: Sum of penalty charges incurred in the period.
    grain_scope: Order/month.
    unit_format: EUR (2 decimals)
    interpretation: Lower is better; high penalties signal delivery or quality issues.
  technical:
    dax_name: Penalty Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Controller
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Penalties reconciled to claims ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: plan.forecast.service_impact.pct
  kpi_key: Service Impact %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
    - Forecast Planning
  use_case_ref:
    - SCM-003
    - SCM-002
    - SCM-001
  calc_type: rate
  business:
    purpose: Quantifies how much of the service loss (stockouts or OTIF misses) is attributable to forecast under-coverage (units-based demand forecast).
    definition: Service Impact % = Stockout Impact % x (Under-Forecast Lost Demand / Total Lost Demand). Under-forecast is defined as a negative forecast error below a configurable threshold; all inputs are unit-based (qty), not revenue.
    grain_scope: Calculated at location_sku_day or sku_week; reported at sku_month aggregated by Date, Org, Product.
    unit_format: "%"
    interpretation: Lower values are better; high impact indicates forecast under-coverage driving service loss.
  technical:
    dax_name: Service Impact %
    depends_on_measures:
      - Stockout Impact %
      - Under-Forecast Lost Demand Share
    lineage:
      - fact_forecast.Forecast Qty
      - fact_demand.Actual Demand Qty
      - fact_stockout.Lost Demand Qty
      - fact_stockout.Demand Qty
      - fact_stockout.Stockout Flag (or fact_otif.OTIF Flag)
  governance:
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
      - KPI only valid when Total Demand Qty > 0.
      - Service Impact % must be <= Stockout Impact %.
      - Under-Forecast Lost Demand Share must be between 0 % and 100 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.7
    last_review: TBD

- kpi_id: ops.oee.pct
  kpi_key: Overall Equipment Effectiveness (OEE) %
  kpi_type: percentage
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  calc_type: ratio
  business:
    purpose: Measures manufacturing performance combining availability, performance, and quality.
    definition: Availability % * Performance % * Quality %
    grain_scope: Production line; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher OEE indicates better utilization; capped at 100 %.
  technical:
    dax_name: OEE %
    depends_on_measures:
    - Availability %
    - Performance %
    - Quality %
    lineage:
    - fact_mes.Availability
    - fact_mes.Performance
    - fact_mes.Quality
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: MES Analyst
    review_cycle: quarterly
    validation_process: automated + manual spot checks
    qa_rules:
    - Subcomponents validated against MES feed; OEE = 100 %
    version: v2.0
  metadata_quality:
    completeness_score: 0.98
    last_review: 12.10.2025
```

## KPIs - Supporting / Diagnostic

```yaml
- kpi_id: ops.failure.count
  kpi_key: Failure Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: count
  business:
    purpose: Counts equipment or process failures in the period.
    definition: Count of recorded failure events.
    grain_scope: Asset or line; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate lower reliability.
  technical:
    dax_name: Failure Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Failures reconcile with maintenance logs.
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.inventory.value.amount
  kpi_key: Inventory Value Amount
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - OPS-002
  calc_type: amount
  business:
    purpose: Tracks inventory value for maintenance-relevant items.
    definition: Sum of inventory value amount for the selected scope.
    grain_scope: SKU/location; aggregated by period.
    unit_format: EUR (2 decimals)
    interpretation: Higher values indicate more capital tied in spare parts.
  technical:
    dax_name: Inventory Value Amount
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.planned_output.units
  kpi_key: Planned Output Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - OPS-003
  calc_type: count
  business:
    purpose: Captures planned production output volume.
    definition: Sum of planned output units for the period.
    grain_scope: Line/site; aggregated by period.
    unit_format: units
    interpretation: Baseline for comparing actual throughput.
  technical:
    dax_name: Planned Output Units
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Production Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.pm.task.count
  kpi_key: Preventive Maintenance Task Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: count
  business:
    purpose: Counts preventive maintenance tasks executed or scheduled.
    definition: Count of PM tasks in the period.
    grain_scope: Asset; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate more planned maintenance activity.
  technical:
    dax_name: Preventive Maintenance Task Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Maintenance
    data_owner: Maintenance BI
    steward: Maintenance Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.production.volume
  kpi_key: Production Volume Units
  kpi_type: quantity
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  - OPS-001
  calc_type: count
  business:
    purpose: Measures total produced volume in units.
    definition: Sum of produced units for the period.
    grain_scope: Line/site; aggregated by period.
    unit_format: units
    interpretation: Higher values indicate higher output.
  technical:
    dax_name: Production Volume Units
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Production Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.quality.defect_rate.pct
  kpi_key: Quality Defect Rate %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  - OPS-001
  calc_type: rate
  business:
    purpose: Measures share of defective units in production.
    definition: Defective Units / Total Produced Units.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Lower values indicate better quality.
  technical:
    dax_name: Quality Defect Rate %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Quality
    data_owner: Quality BI
    steward: Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.safety.incident.count
  kpi_key: Safety Incident Count
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: count
  business:
    purpose: Counts safety incidents recorded in the period.
    definition: Count of recorded safety incidents.
    grain_scope: Site; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate higher safety risk.
  technical:
    dax_name: Safety Incident Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: EHS Manager
    data_owner: EHS BI
    steward: Safety Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.service_level.pct
  kpi_key: Operations Service Level %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-001
  - FIN-002
  calc_type: rate
  business:
    purpose: Measures on-time or in-full performance for operational delivery.
    definition: On-Time or In-Full Deliveries / Total Deliveries.
    grain_scope: Site/product; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better service performance.
  technical:
    dax_name: Operations Service Level %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.yield.pct
  kpi_key: Yield %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - FIN-002
  - OPS-002
  calc_type: rate
  business:
    purpose: Measures ratio of good output to total input.
    definition: Good Units / Total Units Produced.
    grain_scope: Line/shift; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher yield indicates better process efficiency.
  technical:
    dax_name: Yield %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Manufacturing
    data_owner: Manufacturing BI
    steward: Process Engineer
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: order.lines
  kpi_key: Order Lines Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - SCM-002
  - SCM-003
  calc_type: count
  business:
    purpose: Counts order lines processed in the period.
    definition: Count of order line items.
    grain_scope: Order line; aggregated by period and channel.
    unit_format: count
    interpretation: Higher counts indicate higher order volume.
  technical:
    dax_name: Order Lines Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Order Management Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: plans.count
  kpi_key: Plans Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Forecast Planning
  use_case_ref:
  - SCM-002
  - SCM-003
  calc_type: count
  business:
    purpose: Counts planning cycles or plan versions in the period.
    definition: Count of plan records or plan versions.
    grain_scope: Plan; aggregated by period.
    unit_format: count
    interpretation: Higher counts indicate more planning activity.
  technical:
    dax_name: Plans Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: shipments.count
  kpi_key: Shipments Count
  kpi_type: count
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - SCM-001
  - SCM-002
  - SCM-003
  calc_type: count
  business:
    purpose: Counts shipments executed in the period.
    definition: Count of shipment records.
    grain_scope: Shipment; aggregated by period and carrier.
    unit_format: count
    interpretation: Higher counts indicate higher fulfillment activity.
  technical:
    dax_name: Shipments Count
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Logistics
    data_owner: Logistics BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: scm.service_level.pct
  kpi_key: Supply Chain Service Level %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Supply Chain
  use_case_ref:
  - FIN-001
  calc_type: rate
  business:
    purpose: Measures supply chain service level performance.
    definition: On-Time In-Full Orders / Total Orders.
    grain_scope: Customer/order; aggregated by period.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate better service reliability.
  technical:
    dax_name: Supply Chain Service Level %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain
    data_owner: Supply Chain BI
    steward: Service Level Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules: []
    version: v0.1
  metadata_quality:
    completeness_score: 0.6
    last_review: TBD

- kpi_id: ops.availability.pct
  kpi_key: Availability %
  kpi_type: percentage
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Uptime share relative to planned production time.
    definition: Available time / Planned time
    grain_scope: Machine/line level; per shift or day, aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher availability indicates less downtime; low values typically reflect maintenance or scheduling issues.
  technical:
    dax_name: Availability %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Availability % bounded between 0 % and 100 %; reconciles to planned/available time from MES within +/- 1 pp.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.otif.pct
  kpi_key: OTIF %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: null
  domain_tag:
  - Operational Efficiency
  use_case_ref: []
  calc_type: rate
  business:
    purpose: Delivery reliability measured by orders delivered on-time and in-full.
    definition: On-Time In-Full deliveries / Total Deliveries
    grain_scope: Order/shipment level; aggregated weekly/monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher OTIF indicates better delivery reliability; low values reflect service and execution issues.
  technical:
    dax_name: OTIF %
    depends_on_measures:
    - OTIF Deliveries Count
    - Total Deliveries Count
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Finance
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory days reconcile to inventory and COGS within +/- 1 day
    - 'Bounded: DSO/DIO/DPO derived days must be >= 0'
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.working_capital.ccc.days
  kpi_key: Cash Conversion Cycle (Days)
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-001
  - COR-004
  calc_type: amount
  business:
    purpose: Combines receivables, inventory, and payables days to show cash efficiency.
    definition: DSO + DIO - DPO.
    grain_scope: Company / region level.
    unit_format: days
    interpretation: Lower CCC means faster cash conversion and lower working capital.
  technical:
    dax_name: Cash Conversion Cycle (Days)
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Input metrics reconciled before aggregation
    version: v1.1
  metadata_quality:
    completeness_score: 0.8
    last_review: 11.11.2025
  aliases:
  - fin.liquidity.cash_conversion_cycle_days

- kpi_id: ops.downtime.pct
  kpi_key: Downtime %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: rate
  business:
    purpose: Measures share of planned production time lost to downtime.
    definition: Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; analyze downtime drivers and loss categories.
  technical:
    dax_name: Downtime %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Operations Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned Time Minutes > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.downtime.unplanned.pct
  kpi_key: Unplanned Downtime %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - OPS-002
  calc_type: rate
  business:
    purpose: Measures unplanned downtime share of planned time.
    definition: Unplanned Downtime Minutes / Planned Time Minutes.
    grain_scope: Line/day aggregated to plant and period.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; track reliability and maintenance effectiveness.
  technical:
    dax_name: Unplanned Downtime %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Operations
    data_owner: Operations BI
    steward: Maintenance Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Planned Time Minutes > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: inv.turnover
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  calc_type: ratio
  business:
    purpose: Measures how often inventory is sold and replaced.
    definition: COGS / Average Inventory.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: turns
    interpretation: Higher turnover indicates better inventory velocity; too high may risk stockouts.
  technical:
    dax_name: Inventory Turnover
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - COGS and inventory reconciled to ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
  aliases:
  - ops.inventory.turnover

- kpi_id: ops.inventory.turnover
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-001
  calc_type: ratio
  business:
    purpose: Measures how often inventory is sold and replaced.
    definition: COGS / Average Inventory.
    grain_scope: SKU/location; aggregated monthly.
    unit_format: turns
    interpretation: Higher turnover indicates better inventory velocity; too high may risk stockouts.
  technical:
    dax_name: Inventory Turnover
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Inventory Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - COGS and inventory reconciled to ledger
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: plan.forecast.mape.pct
  kpi_key: Forecast MAPE %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-003
  calc_type: rate
  business:
    purpose: Measures mean absolute percentage error in forecast.
    definition: Mean(|Forecast - Actual| / Actual).
    grain_scope: SKU/week; aggregated monthly.
    unit_format: '% (1 decimal)'
    interpretation: Lower is better; high MAPE indicates unstable demand or poor model fit.
  technical:
    dax_name: Forecast MAPE %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Supply Planning Lead
    data_owner: Supply Chain BI
    steward: Planner
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Actual Demand > 0
    - Review outliers for promotions or anomalies
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: supply.in_full.pct
  kpi_key: In-Full %
  kpi_type: diagnostic
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operational Efficiency
  use_case_ref:
  - SCM-002
  calc_type: rate
  business:
    purpose: Measures share of deliveries with complete quantities.
    definition: In-Full Deliveries / Total Deliveries.
    grain_scope: Delivery/day; aggregated weekly or monthly.
    unit_format: '% (1 decimal)'
    interpretation: Higher is better; low values indicate allocation or stock issues.
  technical:
    dax_name: In-Full %
    depends_on_measures: []
    lineage: []
  governance:
    business_owner: Head of Supply Chain / Logistics
    data_owner: Supply Chain BI
    steward: Logistics Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Total Deliveries > 0
    - Value between 0 % and 100 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025
```
