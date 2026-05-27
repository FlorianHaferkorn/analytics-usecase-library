<#
.SYNOPSIS
  Runs the repository quality gate entrypoint.
.DESCRIPTION
  This is intentionally additive for Phase 2 P0: it keeps existing Stage 1 and
  Fabric checks available, then adds the new static report quality gate.
#>
Param(
    [switch]$SkipStage1,
    [switch]$SkipFabric,
    [switch]$IncludeSchema
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.FullName

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
    & $Command
}

if (-not $SkipStage1) {
    Invoke-Step "Stage 1" { & (Join-Path $repoRoot "tooling/run_stage1_checks.ps1") }
}

if (-not $SkipFabric) {
    Invoke-Step "Fabric / Power BI checks" { & (Join-Path $repoRoot "products/fabric/powerbi/tooling/run_fabric_checks.ps1") }
}

Invoke-Step "P0 report quality checks" {
    $reportQuality = Join-Path $repoRoot "products/fabric/powerbi/tooling/validation/check_report_quality.ps1"
    if ($IncludeSchema) {
        & $reportQuality -IncludeSchema
    } else {
        & $reportQuality
    }
}
