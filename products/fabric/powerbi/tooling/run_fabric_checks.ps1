<#
.SYNOPSIS
  Runs Fabric/Power BI-specific validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices).
.DESCRIPTION
  Invokes scripts under products/fabric/powerbi/tooling/validation/ against
  core paths and products/fabric/powerbi/dist. Run from repository root.
  When -AuroraTablesDir is specified, runs the same checks against the Aurora showcase tables directory
  (e.g. showcases/aurora_group/semantic_models/Commercial.SemanticModel/definition/tables).
.EXAMPLE
  .\products\fabric\powerbi\tooling\run_fabric_checks.ps1
.EXAMPLE
  .\products\fabric\powerbi\tooling\run_fabric_checks.ps1 -AuroraTablesDir "showcases/aurora_group/semantic_models/Commercial.SemanticModel/definition/tables"
#>
Param(
  [string]$DistRoot       = "products/fabric/powerbi/dist",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$MeasureDictRoot = "core/semantic_models/domains",
  [string]$AuroraTablesDir = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
# Repo root: products/fabric/powerbi/tooling -> go up 4 levels (tooling -> powerbi -> fabric -> products -> repo)
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.FullName

if (-not (Test-Path (Join-Path $repoRoot "core"))) {
  Write-Error "Repository root not found (expected 'core' under $repoRoot). Run this script from the repository root or ensure path resolution is correct."
  exit 1
}

$distRootResolved = if ([System.IO.Path]::IsPathRooted($DistRoot)) { $DistRoot } else { Join-Path $repoRoot $DistRoot }
$kpiCatalogResolved = if ([System.IO.Path]::IsPathRooted($KpiCatalogRoot)) { $KpiCatalogRoot } else { Join-Path $repoRoot $KpiCatalogRoot }
$measureDictResolved = if ([System.IO.Path]::IsPathRooted($MeasureDictRoot)) { $MeasureDictRoot } else { Join-Path $repoRoot $MeasureDictRoot }

# When -AuroraTablesDir is set, run checks against Aurora showcase tables (single _Measures.tmdl)
$auroraTablesResolved = $null
if ($AuroraTablesDir -and $AuroraTablesDir.Trim().Length -gt 0) {
  $auroraTablesResolved = if ([System.IO.Path]::IsPathRooted($AuroraTablesDir)) { $AuroraTablesDir } else { Join-Path $repoRoot $AuroraTablesDir }
  if (-not (Test-Path $auroraTablesResolved)) {
    Write-Warning "AuroraTablesDir not found: $auroraTablesResolved. Skipping Aurora checks."
    $auroraTablesResolved = $null
  }
}
$checkRoot = if ($auroraTablesResolved) { $auroraTablesResolved } else { $distRootResolved }

$validationDir = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation"
$checkMeasures = Join-Path $validationDir "check_measures_vs_kpi.ps1"
$checkTmdl = Join-Path $validationDir "check_tmdl_vs_measure_dictionary.ps1"
$checkDax = Join-Path $validationDir "check_dax_best_practices.ps1"
  $checkTmdlSyntax = Join-Path $validationDir "check_tmdl_syntax.ps1"
  $checkPbipReadiness = Join-Path $validationDir "check_tmdl_pbip_readiness.ps1"
  $checkDiagramLayout = Join-Path $validationDir "check_diagram_layout.ps1"

  if (-not (Test-Path $checkMeasures)) { Write-Error "Check script not found: $checkMeasures"; exit 1 }
  if (-not (Test-Path $checkTmdl)) { Write-Error "Check script not found: $checkTmdl"; exit 1 }

Push-Location $repoRoot
try {
  $targetLabel = if ($auroraTablesResolved) { "Aurora: $checkRoot" } else { "Dist: $distRootResolved" }
  Write-Host "Fabric/Power BI checks ($targetLabel)..." -ForegroundColor Cyan
  $failed = 0

  if (Test-Path $checkTmdlSyntax) {
    Write-Host ">> check_tmdl_syntax.ps1" -ForegroundColor Cyan
    & $checkTmdlSyntax -DistRoot $checkRoot
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
    Write-Host ""
  }

  if (Test-Path $checkPbipReadiness) {
    Write-Host ">> check_tmdl_pbip_readiness.ps1" -ForegroundColor Cyan
    & $checkPbipReadiness -DistRoot $checkRoot
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
    Write-Host ""
  }

  if (Test-Path $checkDiagramLayout) {
    Write-Host ">> check_diagram_layout.ps1" -ForegroundColor Cyan
    & $checkDiagramLayout -DistRoot $checkRoot
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
    Write-Host ""
  }

  Write-Host ">> check_measures_vs_kpi.ps1" -ForegroundColor Cyan
  & $checkMeasures -DistRoot $checkRoot -KpiCatalogRoot $kpiCatalogResolved
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }

  Write-Host ""
  Write-Host ">> check_tmdl_vs_measure_dictionary.ps1" -ForegroundColor Cyan
  & $checkTmdl -MeasureDictRoot $measureDictResolved -DistRoot $checkRoot
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }

  if (Test-Path $checkDax) {
    Write-Host ""
    Write-Host ">> check_dax_best_practices.ps1" -ForegroundColor Cyan
    & $checkDax -DistRoot $checkRoot
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  if ($auroraTablesResolved) {
    $validateDelta = Join-Path $repoRoot "showcases\aurora_group\data\validate_delta_migration.ps1"
    if (Test-Path $validateDelta) {
      Write-Host ""
      Write-Host ">> validate_delta_migration.ps1 (Aurora gold Delta format)" -ForegroundColor Cyan
      & $validateDelta -SkipStage1
      if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
    }
  }

  $checkReportPages = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation/check_pbip_report_pages.ps1"
  if (Test-Path $checkReportPages) {
    Write-Host ""
    Write-Host ">> check_pbip_report_pages.ps1" -ForegroundColor Cyan
    & $checkReportPages -DistRoot $distRootResolved
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  $checkCompliance = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation/check_page_template_compliance.py"
  if (Test-Path $checkCompliance) {
    Write-Host ""
    Write-Host ">> check_page_template_compliance.py" -ForegroundColor Cyan
    python $checkCompliance --dist-root $distRootResolved
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
