# Script to add missing KPI definitions to catalog

$catalogPath = "core\kpi_catalog\KPI_Catalog.md"
$content = Get-Content -Path $catalogPath -Raw

# Neue KPI Definitionen basierend auf Archiv & Measure Dictionaries
$newKpis = @"

- kpi_id: fin.liquidity.operating_cash_flow
  kpi_key: Operating Cash Flow
  kpi_type: strategic
  kpi_role: strategic
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Measure cash generated from core operations as basis for liquidity steering.
    definition: Net cash inflows from operating activities over the period.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Positive values improve liquidity; negative values may occur during growth or working-capital buildup.
  technical:
    dax_name: Operating Cash Flow
    depends_on_measures:
    - Operating Cash Flow Amount
    lineage:
    - fact_cashflow.OperatingCashFlow
    business_owner: Head of Treasury
    data_owner: Finance BI
    steward: Cash Flow Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Operating cash flow reconciles to cash flow statement within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: fin.liquidity.inventory.amount
  kpi_key: Inventory Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Provide closing inventory value for working capital and liquidity metrics.
    definition: Inventory value at period end at reporting valuation (e.g., standard or average cost).
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher values increase working capital needs; validate against seasonality and service targets.
  technical:
    dax_name: Inventory Amount
    depends_on_measures: []
    lineage: []
    business_owner: Head of Treasury / Supply Chain Finance
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Inventory value reconciles to balance sheet inventory accounts within +/- 0.5 %.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: fin.liquidity.payables.amount
  kpi_key: Payables Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Liquidity
  domain_tag:
  - Finance
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Track accounts payable balances used in DPO and working capital analysis.
    definition: Accounts payable balance at period end.
    grain_scope: Company/segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher balances increase working capital funding but can signal payment delays; compare to terms.
  technical:
    dax_name: Payables Amount
    depends_on_measures: []
    lineage: []
    business_owner: Head of Treasury / Procurement Controlling
    data_owner: Finance BI
    steward: Working Capital Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Payables reconcile to AP ledgers within +/- 0.5 %; non-negative values.
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: ops.planned.hours
  kpi_key: Planned Hours
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Scheduled production time allocated for machines/lines.
    definition: Sum of planned production hours
    grain_scope: Machine/line level; per shift/day, aggregated monthly.
    unit_format: hours
    interpretation: Capacity baseline for utilization and downtime; compare with actual runtime and downtime.
  technical:
    dax_name: Planned Hours
    depends_on_measures: []
    lineage: []
    business_owner: Head of Supply Chain Planning
    data_owner: Supply Chain BI
    steward: Demand Planner
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconcile to planning system within +/- 0.1 h
    - Planned vs actual variance monitored in OEE context
    - Reconciles to WMS/OMS order status within +/- 1 pp
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 04.11.2025

- kpi_id: crm.complaint.rate.pct
  kpi_key: Complaint Rate %
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Customer
  domain_tag:
  - Customer & Market
  use_case_ref:
  - COM-003
  action_code_ref: []
  calc_type: rate
  business:
    purpose: Track complaints normalized by sales volume or customer base.
    definition: Complaint Count / Total Customers (or Orders)
    grain_scope: Complaint / ticket; aggregated to org / channel / product / period.
    unit_format: '% (1 decimal)'
    interpretation: Higher values indicate rising service/quality issues relative to volume; interpret with Complaint Count for absolute context.
  technical:
    dax_name: Complaint Rate %
    depends_on_measures:
    - Customer Complaints Count
    - Active Customers Count
    lineage:
    - fact_experience.Complaint ID
    - dim_customer.CustomerKey
    business_owner: Head of Customer Service
    data_owner: Service BI
    steward: Service Quality Analyst
    review_cycle: monthly
    validation_process: manual review
    qa_rules:
    - Bounded between 0% and 100%; reconciled to service desk reports
    version: v0.1
  metadata_quality:
    completeness_score: 1.0
    last_review: 26.01.2026

- kpi_id: hr.gm.amount
  kpi_key: HR Gross Margin Amount
  kpi_type: supporting
  kpi_role: supporting
  impact_dimension: Profitability
  domain_tag:
  - People & Culture
  use_case_ref: []
  action_code_ref: []
  calc_type: amount
  business:
    purpose: Measure gross margin contribution attributed to HR segments or people-related analyses.
    definition: Net Sales Amount - COGS Amount (HR segment context)
    grain_scope: Company/HR segment; monthly or quarterly closing.
    unit_format: EUR (2 decimals)
    interpretation: Higher values indicate stronger margin contribution from people segments; compare with headcount metrics.
  technical:
    dax_name: HR Gross Margin Amount
    depends_on_measures:
    - Net Sales Amount
    - COGS Amount
    lineage:
    - fact_sales.Net Sales Amount
    - fact_sales.Cost of Goods Sold Amount
    business_owner: Head of HR Controlling
    data_owner: Finance BI
    steward: HR Finance Analyst
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Margin reconciles to finance totals within +/- 0.5 %
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 26.01.2026

- kpi_id: ops.inventory.turnover
  kpi_key: Inventory Turnover
  kpi_type: diagnostic
  kpi_role: strategic
  impact_dimension: Efficiency
  domain_tag:
  - Operations
  - Supply Chain
  use_case_ref:
  - SCM-001
  action_code_ref: []
  calc_type: ratio
  business:
    purpose: Measure how quickly inventory is sold and replaced.
    definition: COGS / Average Inventory
    grain_scope: SKU/Location; aggregated weekly/monthly.
    unit_format: ratio (2 decimals)
    interpretation: Higher turnover indicates efficient inventory management; very high may signal stockout risk.
  technical:
    dax_name: Inventory Turnover
    depends_on_measures:
    - COGS Amount
    - Average Inventory Amount
    lineage:
    - fact_cogs.COGS Amount
    - fact_inventory.Average Inventory Amount
    business_owner: Head of Supply Chain / Finance
    data_owner: Supply Chain BI
    steward: Inventory Controller
    review_cycle: quarterly
    validation_process: manual review
    qa_rules:
    - Non-negative; reconciles to inventory and COGS balances within +/- 0.1
    version: v1.0
  metadata_quality:
    completeness_score: 0.8
    last_review: 26.01.2026
"@

# Finde Einfügepunkt (nach wc.dso.days)
$insertMarker = "- kpi_id: wc.dso.days"
$insertIndex = $content.IndexOf($insertMarker)

if ($insertIndex -gt 0) {
  # Finde das Ende des wc.dso.days Blocks (nächstes "- kpi_id:" oder Ende)
  $nextKpiIndex = $content.IndexOf("`n- kpi_id:", $insertIndex + $insertMarker.Length)
  
  if ($nextKpiIndex -gt 0) {
    $before = $content.Substring(0, $nextKpiIndex)
    $after = $content.Substring($nextKpiIndex)
    $content = $before + $newKpis + $after
  } else {
    # Am Ende einfügen
    $content = $content + $newKpis
  }
  
  Set-Content -Path $catalogPath -Value $content -NoNewline
  Write-Host "Added 7 missing KPI definitions to catalog" -ForegroundColor Green
} else {
  Write-Host "ERROR: Could not find insertion point" -ForegroundColor Red
  exit 1
}
