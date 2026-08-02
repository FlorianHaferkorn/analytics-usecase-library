<#
.SYNOPSIS
  Runs the IBCS-pattern report scorecard (weighted points + knock-outs, R3.3).
.DESCRIPTION
  Wraps tooling/report_quality/report_scorecard.py. Prints a score (0-100%,
  threshold 70%) and any knock-outs (Mixed-Scale, Unsorted Evidence) per
  report to the console/CI log, and writes a JSON results file for CI
  artifact upload.

  Only reports listed in -Enforce actually fail this gate (exit 1) on a
  failing score/knock-out; all other reports are scored and printed for
  visibility but do not block the build -- 17/17 passing is R5.1's job
  (generator rollout), not R3.3's. Default enforced report: COM-002 (the
  verified R1.x pilot). See docs/architecture/ for the full rationale once
  R3.3 is written up.
.PARAMETER DistRoot
  Path to the dist folder containing .Report directories.
.PARAMETER Enforce
  Report-name substrings that fail the gate on a failing score/knock-out.
.PARAMETER WriteResults
  Path to write JSON scorecard results to (CI artifact source).
.EXAMPLE
  .\check_report_scorecard.ps1 -DistRoot "products/fabric/powerbi/dist"
#>
Param(
    [string]$DistRoot = "",
    [string[]]$Enforce = @("COM-002"),
    [string]$WriteResults = "internal/metrics/runs/report_scorecard/latest_results.json"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.Parent.FullName

if (-not $DistRoot) {
    $DistRoot = Join-Path $repoRoot "products/fabric/powerbi/dist"
} elseif (-not [System.IO.Path]::IsPathRooted($DistRoot)) {
    $DistRoot = Join-Path $repoRoot $DistRoot
}
if (-not [System.IO.Path]::IsPathRooted($WriteResults)) {
    $WriteResults = Join-Path $repoRoot $WriteResults
}

$env:PYTHONPATH = @(
    (Join-Path $repoRoot "tooling"),
    $env:PYTHONPATH
) -join [System.IO.Path]::PathSeparator

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
if (-not $pythonCommand) {
    throw "Python 3 not found. Use py -3, python3, or python and ensure one resolves to Python 3."
}

# --fidelity (L11): Treue je Ziel-Werkzeug mitbewerten. Bewusst OHNE --fidelity-floor,
# also ADVISORY. Ein harter Boden waere heute ein Dauer-Rot, solange der Vega-Konnektor
# nicht angebunden ist (Task L9) — und ein Gate, das immer rot ist, wird abgeschaltet
# statt beachtet. Der Boden kommt mit L9; das Release-Gate setzt ihn dann per
# --fidelity-floor, ohne dass hier etwas Neues gebaut werden muss.
$argsList = @(
    "-m", "report_quality.report_scorecard",
    "--dist-root", $DistRoot,
    "--write-results", $WriteResults,
    "--fidelity",
    "--enforce"
) + $Enforce

Write-Host "Report scorecard (IBCS: weighted points + knock-outs, threshold 70%): $DistRoot" -ForegroundColor Cyan
$parts = $pythonCommand -split " "
$exe = $parts[0]
$exeArgs = @()
if ($parts.Count -gt 1) { $exeArgs = @($parts[1..($parts.Count - 1)]) }
$exeArgs += $argsList
& $exe $exeArgs
exit $LASTEXITCODE
