<#
.SYNOPSIS
  Standard adapter command: build -> dist/
.DESCRIPTION
  Reference implementation for the Fabric/Power BI adapter.
  Runs Core gates (optional), builds registry outputs, derives IR, and generates tool artifacts.

  Transitional note:
  Measure generation currently uses existing generators that read Core artifacts.
  Target state is IR-first generation.
#>
Param(
  [Parameter(Mandatory = $true)][string]$UseCaseId,
  [string]$UseCasesRoot   = "core/usecases",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$DistRoot       = "products/fabric_powerbi/dist",
  [switch]$SkipStage1,
  [switch]$SkipIr
)

$ErrorActionPreference = "Stop"

Write-Host "Adapter build (Fabric/Power BI) - UseCaseId=$UseCaseId" -ForegroundColor Cyan

if (-not $SkipStage1) {
  Write-Host ">> Stage 1 gate" -ForegroundColor Cyan
  & ./tooling/run_stage1_checks.ps1
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host ""
}

if (-not $SkipIr) {
  Write-Host ">> Build IR (from Core ABI outputs)" -ForegroundColor Cyan
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 ./tooling/ir/build_ir.py
  } else {
    & python ./tooling/ir/build_ir.py
  }
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host ""
}

Write-Host ">> Generate TMDL measures (existing generator)" -ForegroundColor Cyan
& ./tooling/generation/generate_tmdl_measures.ps1 `
  -UseCase $UseCaseId `
  -UseCasesRoot $UseCasesRoot `
  -KpiCatalogRoot $KpiCatalogRoot `
  -DistRoot $DistRoot `
  -OverwriteExisting

exit $LASTEXITCODE

