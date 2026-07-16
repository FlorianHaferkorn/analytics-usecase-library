<#
.SYNOPSIS
  Runs P0 report quality checks for generated Power BI reports.
.DESCRIPTION
  Wraps the adapter-neutral tooling/report_quality package. By default this runs
  static structural, content, and DAX reference checks without network access.
  Use -IncludeSchema to fetch and cache Microsoft JSON schemas as part of the run.
#>
Param(
    [string]$DistRoot = "",
    [switch]$IncludeSchema,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.Parent.Parent.Parent.FullName

if (-not $DistRoot) {
    $DistRoot = Join-Path $repoRoot "products/fabric/powerbi/dist"
} elseif (-not [System.IO.Path]::IsPathRooted($DistRoot)) {
    $DistRoot = Join-Path $repoRoot $DistRoot
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

$argsList = @(
    "-m", "report_quality.cli",
    "--dist-root", $DistRoot
)
if ($IncludeSchema) { $argsList += "--include-schema" }
if ($Json) { $argsList += "--json" }

Write-Host "Report quality validation: $DistRoot" -ForegroundColor Cyan
$parts = $pythonCommand -split " "
$exe = $parts[0]
$exeArgs = @()
if ($parts.Count -gt 1) { $exeArgs = @($parts[1..($parts.Count - 1)]) }
$exeArgs += $argsList
& $exe $exeArgs
exit $LASTEXITCODE
