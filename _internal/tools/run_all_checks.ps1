Param(
  [string]$UseCasesRoot = "usecases",
  [string]$KpiCatalogRoot = "_includes/kpi_catalog"
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
  return $repo
}

$repoRoot = (Get-Location).Path

$useCasesRoot   = Resolve-RepoPath -ProvidedPath $UseCasesRoot -DefaultRelative 'usecases'
$kpiCatalogRoot = Resolve-RepoPath -ProvidedPath $KpiCatalogRoot -DefaultRelative '_includes/kpi_catalog'

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
Invoke-LocalScript -RelativePath "tools/coverage/validate_factsheets.ps1" -Arguments @("-UseCasesRoot", $useCasesRoot)

# 2) Validate KPI catalogs
Invoke-LocalScript -RelativePath "tools/coverage/validate_kpi_catalog.ps1" -Arguments @("-KpiCatalogRoot", $kpiCatalogRoot)

# 3) Check coverage FactSheet vs KPI catalog
# Let the script resolve roots itself based on repository layout.
Invoke-LocalScript -RelativePath "tools/coverage/check_factsheet_vs_kpi.ps1" -Arguments @()

# 4) Check measures vs KPI catalog
# Let the script use its own defaults (dist and _includes/kpi_catalog).
Invoke-LocalScript -RelativePath "tools/coverage/check_measures_vs_kpi.ps1" -Arguments @()

# 5) Sanity-check docs and tooling references
Invoke-LocalScript -RelativePath "tools/maintenance/check_docs_refs.ps1" -Arguments @()

Write-Host "All checks invoked. Review messages above for warnings or errors." -ForegroundColor Green
