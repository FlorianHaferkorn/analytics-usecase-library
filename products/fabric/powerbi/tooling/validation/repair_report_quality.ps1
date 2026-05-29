<#
.SYNOPSIS
  Run the deterministic self-heal loop on all Power BI reports.

.DESCRIPTION
  Invokes the Python report_quality CLI with --self-heal and writes a JSON fix
  log to internal/metrics/runs/<timestamp>/self_heal_log.json.

  This script is safe to run locally. CI uses detect-only mode (run_fabric_checks.ps1).

.PARAMETER DistRoot
  Path to the dist folder. Defaults to products/fabric/powerbi/dist.

.PARAMETER MaxIterations
  Maximum fix iterations per report. Defaults to 3.

.PARAMETER DryRun
  Report what would be fixed without writing any files.

.PARAMETER Summary
  Compact output suitable for CI logs or agent prompts.

.EXAMPLE
  .\products\fabric\powerbi\tooling\validation\repair_report_quality.ps1
.EXAMPLE
  .\products\fabric\powerbi\tooling\validation\repair_report_quality.ps1 -DryRun
#>
Param(
    [string]$DistRoot = "products/fabric/powerbi/dist",
    [int]$MaxIterations = 3,
    [switch]$DryRun,
    [switch]$Summary,
    [string]$FixLogPath = ""
)

$ErrorActionPreference = "Stop"

# ── Python launcher (py -3 > python3 > python) ──────────────────────────────
$pyExe = $null
foreach ($candidate in @("py", "python3", "python")) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($found) {
        $version = & $candidate --version 2>&1
        if ($version -match "Python 3") {
            $pyExe = $candidate
            break
        }
    }
}
if (-not $pyExe) {
    Write-Error "Python 3 not found. Install Python 3 and ensure it is on PATH."
    exit 1
}

# ── Output path ──────────────────────────────────────────────────────────────
if (-not $FixLogPath) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $runDir = "internal/metrics/runs/$timestamp"
    $FixLogPath = "$runDir/self_heal_log.json"
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
} else {
    New-Item -ItemType Directory -Path (Split-Path -Parent $FixLogPath) -Force -ErrorAction SilentlyContinue | Out-Null
}

# ── Build CLI args ────────────────────────────────────────────────────────────
$cliArgs = @(
    "-m", "tooling.report_quality.cli",
    "--dist-root", $DistRoot,
    "--self-heal",
    "--max-iterations", "$MaxIterations",
    "--write-fix-log", $FixLogPath
)
if ($DryRun) { $cliArgs += "--dry-run" }
if ($Summary) { $cliArgs += "--summary" }

Write-Host ""
Write-Host "== Repair: Report Quality ==" -ForegroundColor Cyan
if ($DryRun) { Write-Host "[DRY-RUN MODE -- no files will be changed]" -ForegroundColor Yellow }

& $pyExe @cliArgs
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "Fix log: $FixLogPath" -ForegroundColor DarkGray

if ($exitCode -eq 0) {
    Write-Host "Repair complete: all reports green." -ForegroundColor Green
} elseif ($exitCode -eq 3) {
    Write-Host "Repair stalled: some violations could not be fixed automatically. Review fix log." -ForegroundColor Yellow
} else {
    Write-Host "Repair exit code: $exitCode" -ForegroundColor Red
}

exit $exitCode
