<#
.SYNOPSIS
  Standard adapter command: validate dist -> report
.DESCRIPTION
  Thin wrapper around existing Fabric/Power BI checks.
#>
Param(
  [string]$DistRoot = "products/fabric_powerbi/dist",
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$MeasureDictRoot = "core/semantic_models/domains",
  [string]$AuroraTablesDir = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Adapter validate (Fabric/Power BI)..." -ForegroundColor Cyan
& ./products/fabric_powerbi/tooling/run_fabric_checks.ps1 `
  -DistRoot $DistRoot `
  -KpiCatalogRoot $KpiCatalogRoot `
  -MeasureDictRoot $MeasureDictRoot `
  -AuroraTablesDir $AuroraTablesDir

exit $LASTEXITCODE

