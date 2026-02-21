<#
.SYNOPSIS
  Standard adapter command: build -> dist/
.DESCRIPTION
  Reference implementation for the Fabric/Power BI adapter.
  Runs Core gates (optional), builds IR from Core ABI + KPI catalog, then generates TMDL from IR only (IR-first).
#>
Param(
  [Parameter(Mandatory = $true)][string]$UseCaseId,
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$DistRoot       = "products/fabric_powerbi/dist",
  [string]$IROutPath      = "tooling/ir/out/ir_v1.json",
  [switch]$SkipStage1,
  # Legacy: run measure generator from Core paths instead of IR (not recommended).
  [switch]$LegacyCorePaths
)

$ErrorActionPreference = "Stop"

Write-Host "Adapter build (Fabric/Power BI) - UseCaseId=$UseCaseId" -ForegroundColor Cyan

if (-not $SkipStage1) {
  Write-Host ">> Stage 1 gate" -ForegroundColor Cyan
  & ./tooling/run_stage1_checks.ps1
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host ""
}

if (-not $LegacyCorePaths) {
  Write-Host ">> Build IR (Core ABI + KPI catalog -> measure_spec)" -ForegroundColor Cyan
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 ./tooling/ir/build_ir.py --kpi-catalog $KpiCatalogRoot --out $IROutPath
  } else {
    & python ./tooling/ir/build_ir.py --kpi-catalog $KpiCatalogRoot --out $IROutPath
  }
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host ""

  Write-Host ">> Generate TMDL measures (IR-first)" -ForegroundColor Cyan
  & ./tooling/generation/generate_tmdl_measures.ps1 `
    -UseCase $UseCaseId `
    -IRPath $IROutPath `
    -DistRoot $DistRoot `
    -OverwriteExisting
} else {
  Write-Host ">> Generate TMDL measures (legacy Core paths)" -ForegroundColor Cyan
  & ./tooling/generation/generate_tmdl_measures.ps1 `
    -UseCase $UseCaseId `
    -UseCasesRoot "core/usecases" `
    -KpiCatalogRoot $KpiCatalogRoot `
    -DistRoot $DistRoot `
    -OverwriteExisting
}

exit $LASTEXITCODE

