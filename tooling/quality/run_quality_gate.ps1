<#
.SYNOPSIS
  Canonical repository quality gate: Stage 1 + Fabric/PBIR checks.
.DESCRIPTION
  Single entry point for local pre-commit and CI. Runs:
    1. tooling/run_stage1_checks.ps1  (governance, docs, YAML, registry)
    2. products/fabric/powerbi/tooling/run_fabric_checks.ps1
       (TMDL, PBIR, pbir-cli --qa, P0 report quality, bindings-adjacent checks)

  Use -SkipStage1 when Stage 1 already ran in the same session (CI stage1 job).

.EXAMPLE
  .\tooling\quality\run_quality_gate.ps1
.EXAMPLE
  .\tooling\quality\run_quality_gate.ps1 -SkipStage1
#>
Param(
    [switch]$SkipStage1,
    [switch]$SkipFabric
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = (Get-Item $scriptDir).Parent.Parent.FullName

$failed = 0

function Invoke-GateStep {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
        $script:failed++
    }
}

if (-not $SkipStage1) {
    Invoke-GateStep "Stage 1" {
        & (Join-Path $repoRoot "tooling/run_stage1_checks.ps1")
    }
}

if (-not $SkipFabric) {
    Invoke-GateStep "Fabric / Power BI checks" {
        & (Join-Path $repoRoot "products/fabric/powerbi/tooling/run_fabric_checks.ps1")
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host "Quality gate: $failed step(s) failed." -ForegroundColor Red
    exit 1
}
Write-Host "Quality gate passed." -ForegroundColor Green
exit 0
