Param(
  [string]$CatalogPath = "framework\kpi_catalog\KPI_Catalog.md"
)

$ErrorActionPreference = "Stop"

Write-Host "Adding missing metadata to KPI Catalog..." -ForegroundColor Cyan

# Domain tag mapping basierend auf KPI-ID Prefix
$domainMap = @{
  'cost.*' = '- Finance'
  'crm.*' = '- Customer & Market'
  'enterprise.*' = '- Enterprise & Governance'
  'fin.*' = '- Finance'
  'inv.*' = '- Supply Chain'
  'margin.*' = '- Finance'
  'ops.*' = '- Operations'
  'order.*' = '- Commercial'
  'people.*' = '- People & Culture'
  'plan.*' = '- Supply Chain'
  'plans.*' = '- Supply Chain'
  'profit.*' = '- Finance'
  'quality.*' = '- Operations'
  'res.*' = '- Operations'
  'sales.*' = '- Commercial'
  'scm.*' = '- Supply Chain'
  'shipments.*' = '- Supply Chain'
  'supply.*' = '- Supply Chain'
  'svc.*' = '- Service & Experience'
  'wc.*' = '- Finance'
}

$content = Get-Content -Path $CatalogPath -Raw

# Liste der KPI IDs ohne domain_tag (aus Report)
$missingTags = @(
  'cost.base_volume.amount', 'cost.cogs_per_unit.amount', 'cost.material.pct', 
  'cost.opex.base.amount', 'cost.opex.vs_plan.pct', 'cost.unit.amount',
  'crm.active_customers.count', 'crm.churned_customers.count', 'crm.clv.amount',
  'crm.complaint.count', 'crm.lifetime_revenue.amount', 'crm.nps.index',
  'crm.retention.pct', 'crm.revenue_at_risk.amount',
  'enterprise.action_outcome_rate.pct', 'enterprise.action_routed.count', 
  'enterprise.value_at_risk.index',
  'fin.cash.balance', 'fin.cash.ocf', 'fin.cash.vs_plan.pct',
  'inv.dio.days', 'inv.obsolete.pct', 'inv.stockout.pct', 'inv.turnover',
  'margin.cogs.pct', 'margin.gm.amount', 'margin.gm.pct', 'margin.gm.vs_plan.pct',
  'margin.promo.gm.pct',
  'ops.availability.pct', 'ops.downtime.pct', 'ops.downtime.unplanned.pct',
  'ops.failure.count', 'ops.inventory.value.amount', 'ops.labor.productivity.pct',
  'ops.mtbf.hours', 'ops.mttr.hours', 'ops.oee.pct', 'ops.otif.pct',
  'ops.performance.pct', 'ops.planned_output.units', 'ops.pm.task.count',
  'ops.pm_compliance.pct', 'ops.production.volume', 'ops.quality.defect_rate.pct',
  'ops.quality.pct', 'ops.safety.incident.count', 'ops.service_level.pct',
  'ops.spare_parts.stockout.pct', 'ops.throughput.units', 
  'ops.working_capital.ccc.days', 'ops.yield.pct',
  'order.lines',
  'people.attrition_risk.pct', 'people.digital_adoption.pct',
  'plan.forecast.accuracy.pct', 'plan.forecast.bias.pct', 'plan.forecast.mape.pct',
  'plan.forecast.service_impact.pct', 'plan.replan.count', 'plans.count',
  'profit.gross_margin',
  'quality.complaint.pct', 'quality.copq.amount', 'quality.defect_density',
  'quality.fpy.pct', 'quality.rework.pct', 'quality.scrap.pct',
  'res.occupancy.pct', 'res.overtime.pct', 'res.shrinkage.pct', 'res.utilization.pct',
  'sales.net_sales.amount', 'sales.net_sales.delta_pct.ly', 
  'sales.net_sales.delta_pct.plan', 'sales.price.realization_pct',
  'sales.promo.cannibalization.pct', 'sales.promo.incremental.amount',
  'sales.promo.roi.pct', 'sales.pvm.mix_effect.amount', 
  'sales.pvm.price_effect.amount', 'sales.pvm.volume_effect.amount', 'sales.units',
  'scm.service_level.pct', 'scm.supplier_risk.score', 'shipments.count',
  'supply.expedite.amount', 'supply.in_full.pct', 'supply.on_time.pct',
  'supply.otif.pct', 'supply.penalty.amount', 'supply.stockout_impact.pct',
  'svc.aht.minutes', 'svc.backlog.count', 'svc.escalation.pct', 'svc.fcr.pct',
  'svc.nps.index', 'svc.sla.attainment.pct', 'svc.tickets.closed.count',
  'svc.tickets.created.count',
  'wc.ccc.days', 'wc.dio.days', 'wc.dpo.days', 'wc.dso.days'
)

$updatedCount = 0

foreach ($kpiId in $missingTags) {
  # Finde passendes Domain Tag
  $domainTag = $null
  foreach ($pattern in $domainMap.Keys) {
    if ($kpiId -like $pattern) {
      $domainTag = $domainMap[$pattern]
      break
    }
  }
  
  if (-not $domainTag) { continue }
  
  # Regex Pattern für diesen KPI Block
  $pattern = "(?ms)(- kpi_id: $([regex]::Escape($kpiId))\s+kpi_key:[^\n]+\s+kpi_type:[^\n]+\s+kpi_role:[^\n]+\s+impact_dimension:[^\n]+\s+domain_tag:\s*)\n"
  
  if ($content -match $pattern) {
    $replacement = "`$1`r`n  $domainTag`r`n"
    $content = $content -replace $pattern, $replacement
    $updatedCount++
    Write-Host "  + $kpiId -> $domainTag" -ForegroundColor Green
  }
}

Set-Content -Path $CatalogPath -Value $content -NoNewline

Write-Host "`nAdded domain_tag to $updatedCount KPIs" -ForegroundColor Green
