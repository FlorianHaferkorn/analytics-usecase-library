Param(
  [string]$UseCasesRoot   = "usecases",
  [string]$KpiCatalogRoot = "framework/kpi_catalog",
  [string]$DistRoot       = "dist"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
  param(
    [string]$ProvidedPath,
    [string]$DefaultRelative
  )
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

$repoRoot = (Get-Location).Path

$useCasesRoot   = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'usecases'
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative 'framework/kpi_catalog'
$distRoot       = Resolve-RepoPath -ProvidedPath $DistRoot -DefaultRelative 'dist'

Write-Host "Running analytics-usecase-library checks..." -ForegroundColor Cyan
Write-Host "UseCases:   $useCasesRoot" -ForegroundColor DarkGray
Write-Host "KPI Catalog: $kpiCatalogRoot" -ForegroundColor DarkGray
Write-Host ""

function Invoke-LocalScript {
  param(
    [string]$RelativePath,
    [string[]]$Arguments
  )
  $full = Join-Path -Path $repoRoot -ChildPath $RelativePath
  if (-not (Test-Path $full)) {
    Write-Host "Skip: $RelativePath (not found)" -ForegroundColor Yellow
    return
  }
  Write-Host ">> $RelativePath $($Arguments -join ' ')" -ForegroundColor Cyan
  try {
    & $full @Arguments
  } catch {
    Write-Host ("  Error while running {0}:{1}  {2}" -f $RelativePath, [Environment]::NewLine, $_.Exception.Message) -ForegroundColor Red
  }
  Write-Host ""
}

# 1) Validate FactSheets
Invoke-LocalScript -RelativePath "_internal/tools/validation/validate_factsheets.ps1" -Arguments @("-UseCasesRoot", $useCasesRoot)

# 2) Validate KPI catalogs
Invoke-LocalScript -RelativePath "_internal/tools/validation/validate_kpi_catalog.ps1" -Arguments @("-KpiCatalogRoot", $kpiCatalogRoot)

# 3) Check coverage FactSheet vs KPI catalog
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_factsheet_vs_kpi.ps1" -Arguments @("-UseCasesRoot", $useCasesRoot, "-KpiCatalogRoot", $kpiCatalogRoot)

# 4) Check measures vs KPI catalog
Invoke-LocalScript -RelativePath "_internal/tools/validation/check_measures_vs_kpi.ps1" -Arguments @("-DistRoot", $distRoot, "-KpiCatalogRoot", $kpiCatalogRoot)

# 5) Sanity-check docs and tooling references
Invoke-LocalScript -RelativePath "_internal/tools/maintenance/check_docs_refs.ps1" -Arguments @()

Write-Host "All checks invoked. Review messages above for warnings or errors." -ForegroundColor Green
