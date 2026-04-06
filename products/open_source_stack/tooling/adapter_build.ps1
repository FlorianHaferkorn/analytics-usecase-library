<#
.SYNOPSIS
  Standard adapter command: build OSS artifacts from Core/IR.
.DESCRIPTION
  Mirrors the Fabric adapter build pattern: optional Stage 1, deterministic IR build,
  then adapter-specific artifact generation. The OSS adapter uses tool-agnostic Core logic
  from the IR and UseCase orchestration/value-driver model; it does not translate DAX into SQL.
#>
Param(
  [string[]]$UseCaseId,
  [switch]$All,
  [string]$KpiCatalogRoot = "core/kpi_catalog",
  [string]$IROutPath = "tooling/ir/out/ir_v1.json",
  [string]$MetricsOutputDir = "products/open_source_stack/dbt_project/models/metrics",
  [string]$PagesOutputDir = "products/open_source_stack/evidence_app/pages",
  [switch]$SkipStage1
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path

function Resolve-PythonLauncher {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @{ Command = "py"; Prefix = @("-3") }
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @{ Command = "python"; Prefix = @() }
  }
  throw "Python launcher not found. Install 'py' or 'python' to build OSS artifacts."
}

function Invoke-Python {
  param([hashtable]$Launcher, [string[]]$Arguments)
  & $Launcher.Command @($Launcher.Prefix) @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Python command failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
  }
}

function Get-UseCasesFromIr {
  param([string]$IrPath)
  $resolved = Join-Path $repoRoot ($IrPath -replace '/', [IO.Path]::DirectorySeparatorChar)
  $ir = Get-Content -Path $resolved -Raw -Encoding utf8 | ConvertFrom-Json
  return @($ir.objects.use_cases.PSObject.Properties.Name | Sort-Object)
}

if (-not $All -and (-not $UseCaseId -or $UseCaseId.Count -eq 0)) {
  throw "Specify -UseCaseId <id> or -All"
}

$launcher = Resolve-PythonLauncher

Write-Host "Adapter build (OSS / Evidence)" -ForegroundColor Cyan

Push-Location $repoRoot
try {
  if (-not $SkipStage1) {
    Write-Host ">> Stage 1 gate" -ForegroundColor Cyan
    & .\tooling\run_stage1_checks.ps1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host ""
  }

  Write-Host ">> Build IR (Core ABI + KPI catalog metadata)" -ForegroundColor Cyan
  Invoke-Python -Launcher $launcher -Arguments @(
    ".\tooling\ir\build_ir.py",
    "--kpi-catalog", $KpiCatalogRoot,
    "--out", $IROutPath
  )
  Write-Host ""

  $selectedUseCases = if ($All) { Get-UseCasesFromIr -IrPath $IROutPath } else { @($UseCaseId | Where-Object { $_ }) }
  if (-not $selectedUseCases -or $selectedUseCases.Count -eq 0) {
    throw "No use cases selected for OSS build."
  }
  $useCaseCsv = ($selectedUseCases -join ",")

  Write-Host ">> Generate dbt metrics (Core logic)" -ForegroundColor Cyan
  Invoke-Python -Launcher $launcher -Arguments @(
    "-m", "products.open_source_stack.tooling.metric_generator.generate_dbt_metrics",
    "--ir-path", $IROutPath,
    "--output-dir", $MetricsOutputDir,
    "--mode", "core",
    "--use-cases", $useCaseCsv
  )
  Write-Host ""

  Write-Host ">> Generate Evidence pages (Core logic)" -ForegroundColor Cyan
  foreach ($useCase in $selectedUseCases) {
    Invoke-Python -Launcher $launcher -Arguments @(
      "-m", "products.open_source_stack.tooling.page_generator.generator",
      "--use-case", $useCase,
      "--ir-path", $IROutPath,
      "--output-dir", $PagesOutputDir
    )
  }
} finally {
  Pop-Location
}

exit 0