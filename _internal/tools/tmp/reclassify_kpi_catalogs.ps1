$ErrorActionPreference = 'Stop'

$strategicIds = @(
  'cost.cogs_per_unit.amount',
  'cost.material.pct',
  'cost.opex.vs_plan.pct',
  'cost.unit.amount',
  'crm.clv.amount',
  'crm.complaint.count',
  'crm.revenue_at_risk.amount',
  'enterprise.action_outcome_rate.pct',
  'inv.dio.days',
  'inv.obsolete.pct',
  'inv.stockout.pct',
  'margin.gm.pct',
  'margin.promo.gm.pct',
  'ops.labor.productivity.pct',
  'ops.mtbf.hours',
  'ops.mttr.hours',
  'ops.performance.pct',
  'ops.pm_compliance.pct',
  'ops.quality.pct',
  'ops.spare_parts.stockout.pct',
  'ops.throughput.units',
  'plan.forecast.accuracy.pct',
  'plan.forecast.bias.pct',
  'plan.forecast.service_impact.pct',
  'plan.replan.count',
  'quality.complaint.pct',
  'quality.copq.amount',
  'quality.defect_density',
  'quality.fpy.pct',
  'quality.rework.pct',
  'quality.scrap.pct',
  'sales.price.realization_pct',
  'sales.promo.cannibalization.pct',
  'sales.promo.roi.pct',
  'sales.pvm.mix_effect.amount',
  'supply.expedite.amount',
  'supply.on_time.pct',
  'supply.otif.pct',
  'supply.penalty.amount',
  'supply.stockout_impact.pct',
  'wc.ccc.days',
  'wc.dio.days',
  'wc.dpo.days',
  'wc.dso.days'
)

function Get-BlockIndices {
  param([string[]]$Lines, [string]$Heading)
  $idx = -1
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i].Trim() -eq $Heading) { $idx = $i; break }
  }
  if ($idx -lt 0) { return $null }
  $start = -1
  for ($i = $idx + 1; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i].Trim() -eq '```yaml') { $start = $i + 1; break }
    if ($Lines[$i].Trim().StartsWith('## ')) { return $null }
  }
  if ($start -lt 0) { return $null }
  $end = -1
  for ($i = $start; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i].Trim() -eq '```') { $end = $i - 1; break }
  }
  if ($end -lt 0) { return $null }
  return @{ start = $start; end = $end; headingIndex = $idx }
}

function Parse-Entries {
  param([string[]]$BlockLines)
  $entries = @()
  $current = @()
  foreach ($line in $BlockLines) {
    if ($line -match '^\s*-\s*kpi_id\s*:') {
      if ($current.Count -gt 0) { $entries += ,$current; $current = @() }
    }
    $current += $line
  }
  if ($current.Count -gt 0) { $entries += ,$current }
  return $entries
}

function Get-KpiId {
  param([string[]]$EntryLines)
  $m = $EntryLines | Select-String -Pattern '^\s*-\s*kpi_id\s*:\s*([\w\.]+)'
  if ($m) { return $m.Matches[0].Groups[1].Value }
  return $null
}

function Update-Entry {
  param([string[]]$EntryLines)
  $updated = @()
  foreach ($line in $EntryLines) {
    if ($line -match '^\s*kpi_type\s*:') { $updated += '  kpi_type: strategic'; continue }
    if ($line -match '^\s*kpi_role\s*:') { $updated += '  kpi_role: strategic'; continue }
    $updated += $line
  }
  return $updated
}

function Has-StrategicRole {
  param([string[]]$EntryLines)
  foreach ($line in $EntryLines) {
    if ($line -match '^\s*kpi_role\s*:\s*strategic\s*$') { return $true }
  }
  return $false
}

function Build-Block {
  param([object[]]$Entries)
  $block = @()
  foreach ($entry in $Entries) { $block += $entry; $block += '' }
  if ($block.Count -gt 0 -and $block[-1] -eq '') { $block = $block[0..($block.Count-2)] }
  return $block
}

$catalogFiles = Get-ChildItem -Path framework\kpi_catalog -Filter "KPI_Catalog_*.md" -File
foreach ($file in $catalogFiles) {
  $lines = Get-Content $file.FullName
  $hasSupportingHeader = $lines | Where-Object { $_.Trim() -eq '## KPIs - Supporting / Diagnostic' }
  $strategicIdx = Get-BlockIndices -Lines $lines -Heading '## KPIs - Strategic'
  if (-not $strategicIdx) { continue }

  if ($hasSupportingHeader) {
    $supportingIdx = Get-BlockIndices -Lines $lines -Heading '## KPIs - Supporting / Diagnostic'
    if (-not $supportingIdx) { continue }

    $strategicLines = @()
    if ($strategicIdx.start -le $strategicIdx.end) { $strategicLines = $lines[$strategicIdx.start..$strategicIdx.end] }
    $supportingLines = @()
    if ($supportingIdx.start -le $supportingIdx.end) { $supportingLines = $lines[$supportingIdx.start..$supportingIdx.end] }

    $allEntries = @()
    $allEntries += (Parse-Entries -BlockLines $strategicLines)
    $allEntries += (Parse-Entries -BlockLines $supportingLines)

    $strategicEntries = @()
    $supportingEntries = @()
    foreach ($entry in $allEntries) {
      if ($entry.Count -eq 0) { continue }
      $id = Get-KpiId -EntryLines $entry
      if ($id -and $strategicIds -contains $id) { $entry = Update-Entry -EntryLines $entry }
      if (Has-StrategicRole -EntryLines $entry) { $strategicEntries += ,$entry } else { $supportingEntries += ,$entry }
    }

    $newStrategicBlock = Build-Block -Entries $strategicEntries
    $newSupportingBlock = Build-Block -Entries $supportingEntries

    $outLines = @()
    for ($i = 0; $i -lt $lines.Count; $i++) {
      if ($i -eq $strategicIdx.start) { $outLines += $newStrategicBlock; $i = $strategicIdx.end; continue }
      if ($i -eq $supportingIdx.start) { $outLines += $newSupportingBlock; $i = $supportingIdx.end; continue }
      $outLines += $lines[$i]
    }
    Set-Content -Path $file.FullName -Value $outLines
  }
  else {
    # Fallback: rebuild with two sections from the single strategic block
    $strategicLines = @()
    if ($strategicIdx.start -le $strategicIdx.end) { $strategicLines = $lines[$strategicIdx.start..$strategicIdx.end] }
    $allEntries = Parse-Entries -BlockLines $strategicLines

    $strategicEntries = @()
    $supportingEntries = @()
    foreach ($entry in $allEntries) {
      if ($entry.Count -eq 0) { continue }
      $id = Get-KpiId -EntryLines $entry
      if ($id -and $strategicIds -contains $id) { $entry = Update-Entry -EntryLines $entry }
      if (Has-StrategicRole -EntryLines $entry) { $strategicEntries += ,$entry } else { $supportingEntries += ,$entry }
    }

    $newStrategicBlock = Build-Block -Entries $strategicEntries
    $newSupportingBlock = Build-Block -Entries $supportingEntries

    $out = @()
    for ($i = 0; $i -le $strategicIdx.headingIndex; $i++) { $out += $lines[$i] }
    $out += ''
    $out += '```yaml'
    $out += $newStrategicBlock
    $out += '```'
    $out += ''
    $out += '## KPIs - Supporting / Diagnostic'
    $out += ''
    $out += '```yaml'
    $out += $newSupportingBlock
    $out += '```'

    $tailStart = $strategicIdx.end + 2
    if ($tailStart -lt $lines.Count) { for ($i = $tailStart; $i -lt $lines.Count; $i++) { $out += $lines[$i] } }
    Set-Content -Path $file.FullName -Value $out
  }
}

$esgPath = 'framework\kpi_catalog\KPI_Catalog_ESG.md'
if (Test-Path $esgPath) {
  $lines = Get-Content $esgPath
  $note = 'This catalog currently contains no strategic KPIs. Any KPIs listed below are supporting/diagnostic and serve explanatory purposes only.'
  $hasNote = $lines | Where-Object { $_ -eq $note }
  if (-not $hasNote) {
    $out = @()
    $inserted = $false
    foreach ($line in $lines) {
      $out += $line
      if (-not $inserted -and $line -like 'Schema: see*') { $out += ''; $out += $note; $inserted = $true }
    }
    if (-not $inserted) { $out = @($note) + $lines }
    Set-Content -Path $esgPath -Value $out
  }
}
