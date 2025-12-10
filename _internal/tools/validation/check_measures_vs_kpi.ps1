Param(
  [string]$DistRoot,
  [string]$KpiCatalogRoot,
  [switch]$FailOnMissing
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
  $repoRoot = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repoRoot -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repoRoot -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Split-KpiChunks {
  param([string]$Block)
  $listMatches = [regex]::Matches($Block, '(?m)^\s*-\s*kpi_id\s*:\s*"?([^"\r\n]+)"?')
  $chunks = @()
  if ($listMatches.Count -gt 0) {
    for ($i = 0; $i -lt $listMatches.Count; $i++) {
      $start = $listMatches[$i].Index
      $end = if ($i -lt $listMatches.Count - 1) { $listMatches[$i + 1].Index } else { $Block.Length }
      $length = $end - $start
      if ($length -gt 0) {
        $chunks += $Block.Substring($start, $length)
      }
    }
  }
  return $chunks
}

function Parse-KpiRecord {
  param([string]$Chunk)
  $idMatch = [regex]::Match($Chunk, '(?m)^\s*-?\s*kpi_id\s*:\s*"?([^"\r\n]+)"?')
  if (-not $idMatch.Success) { return $null }
  return $idMatch.Groups[1].Value
}

function Load-KpiCatalogIndex {
  param([string]$Root)
  $ids = New-Object System.Collections.Generic.HashSet[string]
  Get-ChildItem -Path $Root -Filter '*.md' | Where-Object { $_.Name -ne 'SCHEMA.md' } | ForEach-Object {
    $raw = Get-Content -Raw -Path $_.FullName
    foreach ($match in [regex]::Matches($raw, '(?ms)```yaml\s*(.*?)\s*```')) {
      foreach ($chunk in (Split-KpiChunks -Block $match.Groups[1].Value)) {
        $id = Parse-KpiRecord -Chunk $chunk
        if ($id) { [void]$ids.Add($id) }
      }
    }
  }
  return $ids
}

$resolvedDistRoot = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'dist'
if (-not $resolvedDistRoot) {
  Write-Host "Skip: dist root not found; measures vs KPI check not run." -ForegroundColor Yellow
  exit 0
}

$resolvedKpiRoot = $null
if ($KpiCatalogRoot -and (Test-Path $KpiCatalogRoot)) {
  $resolvedKpiRoot = (Resolve-Path -Path $KpiCatalogRoot).Path
} else {
  $resolvedKpiRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'framework/kpi_catalog'
}
# Defensive: if KPI root resolves identisch zu Dist root, fallback auf framework/kpi_catalog
if ($resolvedKpiRoot -and $resolvedDistRoot -and ($resolvedKpiRoot -eq $resolvedDistRoot)) {
  $fallback = Resolve-RepoPath -ProvidedPath 'framework/kpi_catalog' -DefaultRelative 'framework/kpi_catalog'
  if ($fallback) { $resolvedKpiRoot = $fallback }
}
if (-not $resolvedKpiRoot) { throw "Unable to resolve KPI catalog folder. Provide -KpiCatalogRoot or run inside repository." }

Write-Host "Checking measures vs KPI catalogs..." -ForegroundColor Cyan
Write-Host "  Dist root:      $resolvedDistRoot" -ForegroundColor DarkGray
Write-Host "  KPI catalog:    $resolvedKpiRoot" -ForegroundColor DarkGray

$kpiIndex = Load-KpiCatalogIndex -Root $resolvedKpiRoot
if (-not $kpiIndex) {
  # Defensive fallback so the script does not break when catalog parsing yields no IDs
  $kpiIndex = New-Object System.Collections.Generic.HashSet[string]
}

$measuresFiles = Get-ChildItem -Path $resolvedDistRoot -Recurse -Filter '_Measures.tmdl'
if ($measuresFiles.Count -eq 0) {
  Write-Host "No _Measures.tmdl files found under dist." -ForegroundColor Yellow
  exit 0
}

$missing = @()

foreach ($file in $measuresFiles) {
  $content = Get-Content -Path $file.FullName
  foreach ($line in $content) {
    # Match lines like: /// margin.gm.pct - Gross Margin %
    $m = [regex]::Match($line, '^\s*///\s+([a-zA-Z0-9_\.]+)\s+-\s+')
    if (-not $m.Success) { continue }
    $id = $m.Groups[1].Value
    # Skip "Supporting:" comments etc. which do not look like KPI IDs
    if ($id -notlike '*.*') { continue }
    if (-not $kpiIndex.Contains($id)) {
      $missing += [PSCustomObject]@{
        File = (Resolve-Path -Path $file.FullName).Path
        KpiId = $id
      }
    }
  }
}

if ($missing.Count -eq 0) {
  Write-Host "All KPI references in _Measures.tmdl files exist in KPI catalogs." -ForegroundColor Green
  exit 0
}

Write-Host "Found KPI references in _Measures.tmdl without catalog entry:" -ForegroundColor Yellow
$missing | Sort-Object File, KpiId | Format-Table -AutoSize

if ($FailOnMissing) {
  Write-Error "Missing KPI IDs detected for measures. See list above."
}
