<#
.SYNOPSIS
  Runs Fabric/Power BI-specific validation (measures vs KPI, TMDL vs measure dictionary, DAX best practices).
.DESCRIPTION
  Invokes scripts under products/fabric/powerbi/tooling/validation/ against
  core paths and products/fabric/powerbi/dist. Run from repository root.
  When -AuroraTablesDir is specified, runs the same checks against an additional tables directory.
.EXAMPLE
  .\products\fabric\powerbi\tooling\run_fabric_checks.ps1
.EXAMPLE
  .\products\fabric\powerbi\tooling\run_fabric_checks.ps1 -AuroraTablesDir "products/fabric/powerbi/dist/Commercial.SemanticModel/definition/tables"
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

$pythonCommand = $null
foreach ($cmd in @("py -3", "python3", "python")) {
  try {
    $parts = $cmd -split " "
    $exe = $parts[0]
    $exeArgs = @()
    if ($parts.Count -gt 1) { $exeArgs = @($parts[1..($parts.Count - 1)]) }
    $exeArgs += "--version"
    $ver = (& $exe $exeArgs 2>&1) -join " "
    if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") {
      $pythonCommand = $cmd
      break
    }
  } catch {
    continue
  }
}

function Invoke-Python3 {
  param([string[]]$Arguments)
  if (-not $pythonCommand) {
    throw "Python 3 not found. Use py -3, python3, or python and ensure one resolves to Python 3."
  }
  $parts = $pythonCommand -split " "
  $exe = $parts[0]
  $exeArgs = @()
  if ($parts.Count -gt 1) { $exeArgs = @($parts[1..($parts.Count - 1)]) }
  $exeArgs += $Arguments
  & $exe $exeArgs
}

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
  $checkThemeCompliance = Join-Path $validationDir "check_report_theme_compliance.py"

  if (-not (Test-Path $checkMeasures)) { Write-Error "Check script not found: $checkMeasures"; exit 1 }
  if (-not (Test-Path $checkTmdl)) { Write-Error "Check script not found: $checkTmdl"; exit 1 }

Push-Location $repoRoot
try {
  # Validate pbi-tools binary against lock file before any checks
  $lockFile = Join-Path $repoRoot ".tools/pbi-tools.lock"
  $pbiToolsExe = Join-Path $repoRoot ".tools/pbi-tools/pbi-tools.core.exe"
  if (Test-Path $lockFile) {
    $lockContent = Get-Content $lockFile -Raw
    $sha256Match = [regex]::Match($lockContent, 'sha256\s*:\s*"?([^"\r\n]+)"?')
    if ($sha256Match.Success) { $sha256Val = $sha256Match.Groups[1].Value.Trim() } else { $sha256Val = "" }
    if ($sha256Val) { $expectedHash = $sha256Val.Trim('"') } else { $expectedHash = "placeholder_update_after_download" }
    if (Test-Path $pbiToolsExe) {
      if ($expectedHash -ne "placeholder_update_after_download") {
        $actualHash = (Get-FileHash $pbiToolsExe -Algorithm SHA256).Hash.ToLower()
        if ($actualHash -ne $expectedHash.ToLower()) {
          Write-Error "pbi-tools hash mismatch. Expected $expectedHash, got $actualHash. Re-download per .tools/README.md."
          exit 1
        }
        Write-Host "pbi-tools hash verified OK." -ForegroundColor Green
      } else {
        Write-Warning "pbi-tools.lock contains placeholder SHA-256. Run get-filehash to pin it."
      }
    }
  }

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
    Invoke-Python3 -Arguments @($checkCompliance, "--dist-root", $distRootResolved)
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  if (Test-Path $checkThemeCompliance) {
    Write-Host ""
    Write-Host ">> check_report_theme_compliance.py" -ForegroundColor Cyan
    Invoke-Python3 -Arguments @($checkThemeCompliance, "--dist-root", $distRootResolved)
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  $checkFabInspector = Join-Path $validationDir "check_fab_inspector.ps1"
  if (Test-Path $checkFabInspector) {
    Write-Host ""
    Write-Host ">> check_fab_inspector.ps1 (PBI-Inspector V2 / fab-inspector BPA rules)" -ForegroundColor Cyan
    & $checkFabInspector -DistRoot $distRootResolved
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  $checkReportScorecard = Join-Path $validationDir "check_report_scorecard.ps1"
  if (Test-Path $checkReportScorecard) {
    Write-Host ""
    Write-Host ">> check_report_scorecard.ps1 (IBCS scorecard: weighted points + knock-outs, R3.3)" -ForegroundColor Cyan
    & $checkReportScorecard -DistRoot $distRootResolved
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  $checkSchemaVersions = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation/check_schema_versions.py"
  if (Test-Path $checkSchemaVersions) {
    Write-Host ""
    Write-Host ">> check_schema_versions.py" -ForegroundColor Cyan
    Invoke-Python3 -Arguments @($checkSchemaVersions, "--dist-root", $distRootResolved, "--explain-known-fix")
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 1) { $failed++ }
    # exit 2 = no reports found (warn only, do not fail the gate)
  }

  # ── P0 Report quality checks ─────────────────────────────────────────────
  $checkReportQuality = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation/check_report_quality.ps1"
  if (Test-Path $checkReportQuality) {
    Write-Host ""
    Write-Host ">> check_report_quality.ps1 (P0 static quality)" -ForegroundColor Cyan
    & $checkReportQuality -DistRoot $distRootResolved
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
  }

  # ── PBIR JSON schema validation (all .Report folders) ────────────────────
  $checkPbirSchema = Join-Path $validationDir "check_pbir_schema.ps1"
  if (Test-Path $checkPbirSchema) {
    Write-Host ""
    Write-Host ">> check_pbir_schema.ps1 (PBIR JSON schema, all Reports)" -ForegroundColor Cyan
    $reportDirsForSchema = Get-ChildItem -Path $distRootResolved -Filter "*.Report" -Directory -ErrorAction SilentlyContinue
    if ($reportDirsForSchema) {
      foreach ($rDir in $reportDirsForSchema) {
        Write-Host "   $($rDir.Name)" -ForegroundColor DarkGray
        & $checkPbirSchema -ReportPath $rDir.FullName
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
      }
    } else {
      Write-Host "   No .Report directories found in $distRootResolved" -ForegroundColor Yellow
    }
  }

  # ── pbir-cli structural + quality validation ─────────────────────────────
  # pbir-cli validates report schemas and runs QA checks (hidden visuals,
  # overlapping objects, filter sanity). Does NOT require a live model
  # connection. --qa = schema + quality; --fields requires live XMLA.
  $pbirCliCmd = Get-Command pbir -ErrorAction SilentlyContinue
  if ($pbirCliCmd) {
    Write-Host ""
    Write-Host ">> pbir-cli validate --qa (schema + quality checks)" -ForegroundColor Cyan
    $reportDirs = Get-ChildItem -Path $distRootResolved -Filter "*.Report" -Directory -ErrorAction SilentlyContinue
    if ($reportDirs) {
      foreach ($rDir in $reportDirs) {
        Write-Host "   $($rDir.Name)" -ForegroundColor DarkGray
        & pbir validate $rDir.FullName --qa 2>&1 | ForEach-Object { Write-Host "   $_" }
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) { $failed++ }
      }
    } else {
      Write-Host "   No .Report directories found in $distRootResolved" -ForegroundColor Yellow
    }
  } else {
    Write-Host ""
    Write-Host ">> pbir-cli: not found -- install with 'pip install pbir-cli' to enable schema + QA checks" -ForegroundColor Yellow
  }

  # ── Telemetry: record this run ────────────────────────────────────────────
  $telemetryScript = Join-Path $repoRoot "tooling\generator_core\intelligence\telemetry.py"
  if (Test-Path $telemetryScript) {
    try {
      $runStatus = if ($failed -gt 0) { "failure" } else { "success" }
      $telemetryCode = @"
import sys, json
sys.path.insert(0, r'$repoRoot')
from tooling.generator_core.intelligence.telemetry import TelemetryCollector
from tooling.generator_core.intelligence.classifier import ErrorClassifier
tc = TelemetryCollector()
run = tc.start_run('_fabric_checks', adapter='fabric_checks')
tc.record_phase(run, 'fabric_checks', '$runStatus', errors=['$failed check(s) failed'] if $failed > 0 else [])
tc.complete_run(run)
"@
      Invoke-Python3 -Arguments @("-c", $telemetryCode) 2>$null
    } catch {
      # Non-critical — ignore telemetry errors
    }
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
