<#
.SYNOPSIS
  Proactive SSOT content audit: semantic and consistency checks on KPI catalog (and optionally other SSOTs).
.DESCRIPTION
  Tool-agnostic SSOTs should hold calculation logic; naming (e.g. dax_name) is tool-specific and ideally
  derived from formula + conventions. This script runs in-content checks to surface issues for human review:
  - Possible semantic duplicates (same normalized expression, different KPI IDs)
  - Formula references [MeasureName] not reflected in depends_on_measures
  - Duplicate dax_name (same display name, different IDs)
  Output is written to tooling/validation/results/ and to host. Does not fail the build by default.
.PARAMETER KpiCatalogRoot
  Path to core/kpi_catalog.
.PARAMETER OutputDir
  Directory for report files (default: tooling/validation/results).
.PARAMETER FailOnFinding
  If set, exit 1 when any finding exists (for strict CI).
#>
Param(
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$OutputDir = "",
  [switch]$FailOnFinding
)

$ErrorActionPreference = "Stop"
$script:RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Resolve-RepoPath {
  param([string]$ProvidedPath, [string]$DefaultRelative)
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $script:RepoRoot -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $script:RepoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Get-DependsOnMeasuresFromChunk {
  param([string]$Chunk)
  $key = 'depends_on_measures'
  $list = @()
  if ($Chunk -match "(?m)^\s*$key\s*:\s*\[\s*\]") { return @() }
  $m = [regex]::Match($Chunk, "(?m)^\s*$key\s*:\s*\[(?<inner>[^\]]*)\]")
  if ($m.Success) {
    foreach ($mm in [regex]::Matches($m.Groups['inner'].Value, '(KPI-[A-Z]{3}-\d{3})')) { $list += $mm.Groups[1].Value }
    return $list
  }
  $block = [regex]::Match($Chunk, "(?m)^\s*$key\s*:\s*(?:\r?\n)(?<body>(?:\s{2,}-\s*[^\r\n]+\r?\n?)+)")
  if ($block.Success) {
    $bodyLines = $block.Groups['body'].Value -split "`n"
    foreach ($line in $bodyLines) {
      if ($line -match '^\s{2,}-\s*(KPI-[A-Z]{3}-\d{3})') { $list += $Matches[1] }
    }
    return $list
  }
  $tech = [regex]::Match($Chunk, "(?ms)^\s*technical\s*:\s*\r?\n(.*?)(?=^\s*\w|\z)")
  if ($tech.Success) {
    $sub = $tech.Groups[1].Value
    if ($sub -match "(?m)^\s*$key\s*:\s*\[\s*\]") { return @() }
    $mi = [regex]::Match($sub, "(?m)^\s*$key\s*:\s*\[(?<inner>[^\]]*)\]")
    if ($mi.Success) {
      foreach ($mm in [regex]::Matches($mi.Groups['inner'].Value, '(KPI-[A-Z]{3}-\d{3})')) { $list += $mm.Groups[1].Value }
      return $list
    }
    $blk = [regex]::Match($sub, "(?m)^\s*$key\s*:\s*(?:\r?\n)(?<body>(?:\s{2,}-\s*[^\r\n]+\r?\n?)+)")
    if ($blk.Success) {
      $blkLines = $blk.Groups['body'].Value -split "`n"
      foreach ($line in $blkLines) {
        if ($line -match '^\s{2,}-\s*(KPI-[A-Z]{3}-\d{3})') { $list += $Matches[1] }
      }
    }
  }
  return $list
}

function Get-LiteralBlock {
  param([string]$Chunk, [string]$Key)
  $m = [regex]::Match($Chunk, "(?m)^(\s*)$Key\s*:\s*\|\s*\r?\n")
  if (-not $m.Success) { return $null }
  $keyIndent = $m.Groups[1].Value.Length
  $start = $m.Index + $m.Length
  $lines = @()
  foreach ($line in $Chunk.Substring($start) -split "\r?\n") {
    if ($line -match '^\s*\S' -and $line -match '^(\s*)') {
      if ($matches[1].Length -le $keyIndent) { break }
    }
    $lines += $line
  }
  $nonEmpty = $lines | Where-Object { $_ -match '\S' }
  if ($nonEmpty.Count -eq 0) { return $null }
  $minIndent = ($nonEmpty | ForEach-Object { if ($_ -match '^(\s*)') { $matches[1].Length } else { 0 } } | Measure-Object -Minimum).Minimum
  $joined = ($lines | ForEach-Object { if ($_ -match "^\s{$minIndent}(.*)$") { $matches[1] } else { $_ } }) -join "`n"
  return $joined.Trim()
}

function Get-Scalar {
  param([string]$Chunk, [string]$Key)
  $pat = "(?m)^\s*$([regex]::Escape($Key))\s*:\s*(?:""([^""]*)""|'([^']*)'|([^\s#\r\n]+))"
  $m = [regex]::Match($Chunk, $pat)
  if (-not $m.Success) { return $null }
  $v = $null
  if ($m.Groups[1].Success -and $m.Groups[1].Value) { $v = $m.Groups[1].Value }
  elseif ($m.Groups[2].Success -and $m.Groups[2].Value) { $v = $m.Groups[2].Value }
  elseif ($m.Groups[3].Success -and $m.Groups[3].Value) { $v = $m.Groups[3].Value }
  if (-not $v) { return $null }
  $v = $v.Trim()
  if ($v -match '#') { $v = $v.Split('#')[0].Trim() }
  return $v
}

function Get-ScalarFromTechnical {
  param([string]$Chunk, [string]$Key)
  $tech = [regex]::Match($Chunk, "(?ms)^\s*technical\s*:\s*\r?\n(.*?)(?=^\s*\w|\z)")
  if (-not $tech.Success) { return $null }
  return Get-Scalar -Chunk $tech.Groups[1].Value -Key $Key
}

function Normalize-Expression {
  param([string]$Expr)
  if (-not $Expr) { return "" }
  $s = $Expr -replace '\s+', ' ' -replace '\s*\(\s*', '(' -replace '\s*\)\s*', ')' -replace '\s*,\s*', ',' -replace '^\s+|\s+$', ''
  return $s.ToLowerInvariant()
}

# Extract measure references [Name] from expression (exclude table[column] which contain "[" inside brackets)
function Get-MeasureRefsFromExpression {
  param([string]$Expr)
  if (-not $Expr) { return @() }
  $refs = @()
  foreach ($m in [regex]::Matches($Expr, '\[([^\]]+)\]')) {
    $inner = $m.Groups[1].Value.Trim()
    if ($inner -and $inner -notmatch '\[') { $refs += $inner }
  }
  return $refs | Select-Object -Unique
}

$catalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'core/kpi_catalog'
if (-not $catalogRoot) { throw "KPI catalog root not found. Use -KpiCatalogRoot or run from repo." }
$outDir = if ($OutputDir) {
  $resolved = Resolve-RepoPath -ProvidedPath $OutputDir -DefaultRelative $null
  if ($resolved) { $resolved } else { Join-Path $script:RepoRoot $OutputDir }
} else {
  Join-Path $script:RepoRoot "tooling\validation\results"
}
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

$entryRegex = '(?ms)^\s*-\s*kpi_id\s*:\s*.*?(?=^\s*-\s*kpi_id\s*:|\z)'
$allKpis = @()
Get-ChildItem -Path $catalogRoot -Filter '*.md' | Where-Object { $_.Name -notin @('README.md','SCHEMA.md') } | ForEach-Object {
  $raw = Get-Content -Raw -Path $_.FullName
  foreach ($block in [regex]::Matches($raw, '```yaml\s*(.*?)```', 'Singleline')) {
    $yaml = $block.Groups[1].Value
    foreach ($entry in [regex]::Matches($yaml, $entryRegex)) {
      $chunk = $entry.Value
      $id = ([regex]::Match($chunk, 'kpi_id\s*:\s*([^\s"\r\n]+)')).Groups[1].Value.Trim().Trim('"')
      if (-not $id) { continue }
      $daxExpr = Get-LiteralBlock -Chunk $chunk -Key 'dax_expression'
      if (-not $daxExpr -and $chunk -match 'technical:') {
        $sub = [regex]::Match($chunk, "(?ms)technical:\s*\r?\n(.*?)(?=^\s*\w|\z)").Groups[1].Value
        $daxExpr = Get-LiteralBlock -Chunk $sub -Key 'dax_expression'
      }
      if (-not $daxExpr) { $daxExpr = Get-Scalar -Chunk $chunk -Key 'dax_expression'; if (-not $daxExpr) { $daxExpr = Get-ScalarFromTechnical -Chunk $chunk -Key 'dax_expression' } }
      $daxName = Get-Scalar -Chunk $chunk -Key 'dax_name'; if (-not $daxName) { $daxName = Get-ScalarFromTechnical -Chunk $chunk -Key 'dax_name' }
      $kpiKey = Get-Scalar -Chunk $chunk -Key 'kpi_key'
      $depIds = Get-DependsOnMeasuresFromChunk -Chunk $chunk
      $allKpis += [pscustomobject]@{
        kpi_id = $id
        kpi_key = $kpiKey
        dax_name = $daxName
        dax_expression = $daxExpr
        depends_on_measures = @($depIds)
        file = $_.Name
      }
    }
  }
}

$findings = @()
$byNormalizedExpr = @{}
$byDaxName = @{}

foreach ($k in $allKpis) {
  $norm = Normalize-Expression -Expr $k.dax_expression
  if ($norm) {
    if (-not $byNormalizedExpr[$norm]) { $byNormalizedExpr[$norm] = @() }
    $byNormalizedExpr[$norm] += $k.kpi_id
  }
  if ($k.dax_name) {
    $dn = $k.dax_name.Trim()
    if (-not $byDaxName[$dn]) { $byDaxName[$dn] = @() }
    $byDaxName[$dn] += $k.kpi_id
  }
}

# Possible semantic duplicates
foreach ($norm in $byNormalizedExpr.Keys) {
  $ids = $byNormalizedExpr[$norm]
  if ($ids.Count -gt 1) {
    $findings += [pscustomobject]@{
      Severity = 'Warning'
      Rule = 'SSOT.possible_semantic_duplicate'
      Message = "Same normalized expression used by multiple KPIs (consider one canonical ID): $($ids -join ', ')"
      Location = ''
      Remediation = "Keep one KPI as canonical; reference it in depends_on_measures and brackets. Remove or alias the other(s)."
    }
  }
}

# Duplicate dax_name
foreach ($dn in $byDaxName.Keys) {
  $ids = $byDaxName[$dn]
  if ($ids.Count -gt 1) {
    $findings += [pscustomobject]@{
      Severity = 'Warning'
      Rule = 'SSOT.duplicate_dax_name'
      Message = "dax_name '$dn' used by multiple KPIs: $($ids -join ', '). Tool output (e.g. TMDL) may conflict."
      Location = $dn
      Remediation = "Use a single KPI for this measure name, or derive names from formula (tool-agnostic catalog)."
    }
  }
}

# dax_name -> kpi_id map for resolving [MeasureName]
$nameToId = @{}
foreach ($k in $allKpis) {
  if ($k.dax_name) { $nameToId[$k.dax_name.Trim()] = $k.kpi_id }
}

# Formula references not in depends_on_measures (exclude self: ref name = this KPI's dax_name)
$catalogRelPath = $catalogRoot.Replace($script:RepoRoot, '').TrimStart('/', '\')
if (-not $catalogRelPath) { $catalogRelPath = "core/kpi_catalog" }
foreach ($k in $allKpis) {
  if (-not $k.dax_expression) { continue }
  $refs = Get-MeasureRefsFromExpression -Expr $k.dax_expression
  $depSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$k.depends_on_measures)
  $myName = if ($k.dax_name) { $k.dax_name.Trim() } else { '' }
  foreach ($ref in $refs) {
    if ($ref -eq $myName) { continue }
    $refId = $nameToId[$ref]
    if ($refId -and -not $depSet.Contains($refId)) {
      $kpiCatalogFile = Join-Path $catalogRelPath $k.file
      $insertableLine = "    - $refId"
      $findings += [pscustomobject]@{
        Severity = 'Warning'
        Rule = 'SSOT.formula_ref_not_in_depends_on'
        Message = "KPI '$($k.kpi_id)' formula references [$ref] but depends_on_measures does not include '$refId'."
        Location = $k.kpi_id
        Remediation = "Add $refId to technical.depends_on_measures for $($k.kpi_id) in the KPI catalog."
        InsertableRemediation = [pscustomobject]@{
          ssot_type = 'kpi_catalog'
          file_path = $kpiCatalogFile.Replace('\', '/')
          insert_location = "In the YAML block with kpi_id: $($k.kpi_id), under technical.depends_on_measures: add the following line (after the last existing - <id> or after depends_on_measures: if empty)."
          insertable_content = $insertableLine
        }
      }
    }
  }
}

# Report
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmm'
$reportPath = Join-Path $outDir "ssot_audit_$timestamp.md"
$jsonPath = Join-Path $outDir "ssot_audit_$timestamp.json"

$md = @"
# SSOT Content Audit Report
Generated: $(Get-Date -Format 'o')
Source: KPI catalog ($catalogRoot)
Findings: $($findings.Count)

## Summary
- **Possible semantic duplicates (same expression):** $($findings | Where-Object { $_.Rule -eq 'SSOT.possible_semantic_duplicate' } | Measure-Object | Select-Object -ExpandProperty Count)
- **Duplicate dax_name:** $($findings | Where-Object { $_.Rule -eq 'SSOT.duplicate_dax_name' } | Measure-Object | Select-Object -ExpandProperty Count)
- **Formula ref not in depends_on_measures:** $($findings | Where-Object { $_.Rule -eq 'SSOT.formula_ref_not_in_depends_on' } | Measure-Object | Select-Object -ExpandProperty Count)

## Findings
"@
foreach ($f in $findings) {
  $md += "`n### [$($f.Severity)] $($f.Rule)`n$($f.Message)`n- **Remediation:** $($f.Remediation)`n"
  if ($f.InsertableRemediation) {
    $ir = $f.InsertableRemediation
    $md += "- **Insertable (SSOT: $($ir.ssot_type)):** File ``$($ir.file_path)``.`n"
    $md += "- **Insert location:** $($ir.insert_location)`n"
    $md += "``````yaml`n$($ir.insertable_content)`n```````n"
  }
}
$md | Set-Content -Path $reportPath -Encoding UTF8

$findings | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding UTF8

Write-Host "SSOT content audit: $($findings.Count) finding(s). Report: $reportPath" -ForegroundColor $(if ($findings.Count -eq 0) { 'Green' } else { 'Yellow' })
foreach ($f in $findings) {
  Write-Host "  [$($f.Severity)] $($f.Rule): $($f.Message)" -ForegroundColor Gray
}

if ($FailOnFinding -and $findings.Count -gt 0) { exit 1 }
exit 0
