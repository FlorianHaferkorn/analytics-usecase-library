<#
.SYNOPSIS
  Runs Fabric/Power BI-specific validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices).
.DESCRIPTION
  Invokes scripts under implementations/microsoft_fabric_powerbi/validation/ against
  framework paths and implementations/microsoft_fabric_powerbi/dist. Run from repository root.
.EXAMPLE
  .\implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1
#>
Param(
  [string]$DistRoot       = "implementations/microsoft_fabric_powerbi/dist",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$MeasureDictRoot = "framework/semantic_models/domains"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
# Repo root: implementations/microsoft_fabric_powerbi/tools -> go up 3 levels
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.FullName

if (-not (Test-Path (Join-Path $repoRoot "framework"))) {
  Write-Error "Repository root not found (expected 'framework' under $repoRoot). Run this script from the repository root or ensure path resolution is correct."
  exit 1
}

$distRootResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot $DistRoot }
$kpiCatalogResolved = if ([System.IO.Path]::IsPathRooted($KpiCatalogRoot)) { $KpiCatalogRoot } else { Join-Path $repoRoot $KpiCatalogRoot }
$measureDictResolved = if ([System.IO.Path]::IsPathRooted($MeasureDictRoot)) { $MeasureDictRoot } else { Join-Path $repoRoot $MeasureDictRoot }

$validationDir = Join-Path $repoRoot "implementations/microsoft_fabric_powerbi/validation"
$checkMeasures = Join-Path $validationDir "check_measures_vs_kpi.ps1"
$checkTmdl = Join-Path $validationDir "check_tmdl_vs_measure_dictionary.ps1"
$checkDax = Join-Path $validationDir "check_dax_best_practices.ps1"

if (-not (Test-Path $checkMeasures)) { Write-Error "Check script not found: $checkMeasures"; exit 1 }
if (-not (Test-Path $checkTmdl)) { Write-Error "Check script not found: $checkTmdl"; exit 1 }

Push-Location $repoRoot
try {
  Write-Host "Fabric/Power BI checks (Dist: $distRootResolved)..." -ForegroundColor Cyan
  $failed = 0

  Write-Host ">> check_measures_vs_kpi.ps1" -ForegroundColor Cyan
  & $checkMeasures -DistRoot $distRootResolved -KpiCatalogRoot $kpiCatalogResolved
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }

  Write-Host ""
  Write-Host ">> check_tmdl_vs_measure_dictionary.ps1" -ForegroundColor Cyan
  & $checkTmdl -MeasureDictRoot $measureDictResolved -DistRoot $distRootResolved
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }

  if (Test-Path $checkDax) {
    Write-Host ""
    Write-Host ">> check_dax_best_practices.ps1" -ForegroundColor Cyan
    & $checkDax -DistRoot $distRootResolved
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  if ($failed -gt 0) {
    Write-Host "Fabric checks: $failed failed." -ForegroundColor Red
    exit 1
  }
  Write-Host "Fabric checks passed." -ForegroundColor Green
  exit 0
} finally {
  Pop-Location
}
