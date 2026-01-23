Param(
  [string]$ActionCodesRoot = "framework/action_codes",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [switch]$FailOnError
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param([string]$ProvidedPath,[string]$DefaultRelative)
  $repo = (Get-Location).Path
  if ($ProvidedPath) {
    if (Test-Path $ProvidedPath) { return (Resolve-Path -Path $ProvidedPath).Path }
    $candidate = Join-Path -Path $repo -ChildPath $ProvidedPath
    if (Test-Path $candidate) { return (Resolve-Path -Path $candidate).Path }
  }
  if ($DefaultRelative) {
    $fallback = Join-Path -Path $repo -ChildPath $DefaultRelative
    if (Test-Path $fallback) { return (Resolve-Path -Path $fallback).Path }
  }
  return $null
}

function Get-KpiIdsFromCatalog {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -Filter "KPI_Catalog.md" | Where-Object {
    $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*-\s*kpi_id\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[1])
      }
    }
  }
  return $ids
}

function Get-KpiIdsFromActionCodes {
  param([string]$Root)
  $ids = [System.Collections.Generic.HashSet[string]]::new()
  Get-ChildItem -Path $Root -Recurse -File | Where-Object {
    $_.Extension -in @(".yaml",".yml") -and $_.FullName -notmatch '\\_internal\\archive\\'
  } | ForEach-Object {
    Get-Content -Path $_.FullName | ForEach-Object {
      if ($_ -match '^\s*(kpi_id|metric_kpi_id)\s*:\s*"?([^"\s]+)"?') {
        $null = $ids.Add($matches[2])
      }
    }
  }
  return $ids
}

$actionCodesRoot = Resolve-RepoPath -ProvidedPath $ActionCodesRoot -DefaultRelative "framework/action_codes"
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative "framework/kpi_catalog"
if (-not $actionCodesRoot) { throw "Action codes root not found. Provide -ActionCodesRoot or run inside repository." }
if (-not $kpiCatalogRoot) { throw "KPI catalog root not found. Provide -KpiCatalogRoot or run inside repository." }

Write-Host "Action Codes -> KPI Catalog consistency" -ForegroundColor Cyan
$catalogIds = Get-KpiIdsFromCatalog -Root $kpiCatalogRoot
$actionIds = Get-KpiIdsFromActionCodes -Root $actionCodesRoot

$missing = $actionIds | Where-Object { -not $catalogIds.Contains($_) } | Sort-Object

if ($missing.Count -gt 0) {
  Write-Host "Missing in KPI Catalog (referenced in action codes):" -ForegroundColor Red
  $missing | ForEach-Object { Write-Host "  - $_" }
  if ($FailOnError) { exit 1 }
  exit 0
}

Write-Host "OK: action code KPI references are consistent." -ForegroundColor Green

