# generate_aurora_pbip.ps1
# Reproducible Brackets → PBIP pipeline entrypoint for the Aurora analytics showcase.
#
# Reads UseCase_Bracket.yaml files, generates TMDL semantic models and PBIR report pages,
# verifies the PBIP output is loadable in Power BI Desktop, and checks page-template compliance.
#
# Run from the repository root.
#
# Examples:
#   .\generate_aurora_pbip.ps1 -UseCase COM-001
#   .\generate_aurora_pbip.ps1 -Domain Commercial
#   .\generate_aurora_pbip.ps1 -All
#   .\generate_aurora_pbip.ps1 -ConfigFile aurora_scope.json
#   .\generate_aurora_pbip.ps1 -All -SkipVerification -DryRun

Param(
    # Scope: exactly one of these must be set
    [string]$UseCase,
    [string]$Domain,
    [switch]$All,
    [string]$ConfigFile,          # JSON: { "use_cases": ["COM-001", "COM-002"] }

    # Pass-through to orchestrate_full_model.ps1
    [string]$UseCaseRoot    = "core\usecases\core",
    [string]$ConnectionName = "local_pbip",
    [string]$ThemeName,
    [switch]$UseAuroraData,
    [switch]$NoStrictRegistry,
    [switch]$DryRun,

    # Pipeline control
    [switch]$SkipVerification,    # Skip PBIP Desktop-readiness and page-structure checks
    [switch]$SkipCompliance,      # Skip page-template compliance check (Python)
    [string]$DistRoot = "products/fabric/powerbi/dist"
)

$ErrorActionPreference = "Stop"

# ── Path resolution ───────────────────────────────────────────────────────────
$script:RepoRoot = $PSScriptRoot
if (-not ((Test-Path (Join-Path $script:RepoRoot "core")) -and
          (Test-Path (Join-Path $script:RepoRoot "tooling")))) {
    throw "generate_aurora_pbip.ps1 must be run from the repository root (directory containing 'core' and 'tooling')."
}

$orchestratorScript = "products\fabric\powerbi\orchestrator\orchestrate_full_model.ps1"
$desktopReadyScript = "products\fabric\powerbi\tooling\ensure_pbip_desktop_ready.ps1"
$pageCheckScript    = "products\fabric\powerbi\tooling\validation\check_pbip_report_pages.ps1"
$complianceScript   = "products\fabric\powerbi\tooling\validation\check_page_template_compliance.py"

foreach ($required in @($orchestratorScript)) {
    if (-not (Test-Path (Join-Path $script:RepoRoot $required))) {
        throw "Required script not found: $required"
    }
}

# ── Scope resolution ──────────────────────────────────────────────────────────
$modeCount = 0
if ($UseCase)    { $modeCount++ }
if ($Domain)     { $modeCount++ }
if ($All)        { $modeCount++ }
if ($ConfigFile) { $modeCount++ }

if ($modeCount -eq 0) {
    Write-Host @"
Usage:
  .\generate_aurora_pbip.ps1 -UseCase COM-001
  .\generate_aurora_pbip.ps1 -Domain Commercial
  .\generate_aurora_pbip.ps1 -All
  .\generate_aurora_pbip.ps1 -ConfigFile aurora_scope.json

ConfigFile format: { "use_cases": ["COM-001", "COM-002"] }
"@
    exit 1
}
if ($modeCount -gt 1) {
    throw "Specify only one of: -UseCase, -Domain, -All, -ConfigFile"
}

# Resolve scope name and orchestrator args
$scopeLabel = ""
$orchArgs   = @()

if ($UseCase) {
    $scopeLabel = "UseCase: $UseCase"
    $orchArgs   = @("-UseCase", $UseCase)
} elseif ($Domain) {
    $scopeLabel = "Domain: $Domain"
    $orchArgs   = @("-Domain", $Domain)
} elseif ($All) {
    $scopeLabel = "All use cases"
    $orchArgs   = @("-All")
} elseif ($ConfigFile) {
    $cfPath = if ([System.IO.Path]::IsPathRooted($ConfigFile)) { $ConfigFile } else { Join-Path $script:RepoRoot $ConfigFile }
    if (-not (Test-Path $cfPath)) { throw "ConfigFile not found: $cfPath" }
    $cfg = Get-Content -Raw $cfPath | ConvertFrom-Json
    $ucList = @($cfg.use_cases)
    if ($ucList.Count -eq 0) { throw "ConfigFile must contain a non-empty 'use_cases' array" }
    # Orchestrate one at a time for each UC in the config list
    $scopeLabel = "ConfigFile ($($ucList.Count) use cases)"
    $orchArgs   = $null  # handled below in loop
}

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Aurora PBIP Pipeline                                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  Scope:     $scopeLabel" -ForegroundColor White
Write-Host "  DistRoot:  $DistRoot" -ForegroundColor White
if ($DryRun) { Write-Host "  Mode:      DRY RUN (no files written)" -ForegroundColor Yellow }
Write-Host ""

$startTime = Get-Date

# ── Step 1: Generate (orchestrate_full_model.ps1) ─────────────────────────────
Write-Host "── Step 1 / 4  Generate TMDL + PBIP ──────────────────────" -ForegroundColor Cyan

function Invoke-Orchestrator {
    param([array]$ExtraArgs)

    $params = $ExtraArgs + @(
        "-UseCaseRoot",    $UseCaseRoot,
        "-ConnectionName", $ConnectionName
    )
    if ($ThemeName)        { $params += @("-ThemeName", $ThemeName) }
    if ($UseAuroraData)    { $params += "-UseAuroraData" }
    if ($NoStrictRegistry) { $params += "-NoStrictRegistry" }
    if ($DryRun)           { $params += "-DryRun" }

    & (Join-Path $script:RepoRoot $orchestratorScript) @params
    return $LASTEXITCODE
}

$step1OK = $true
if ($orchArgs -ne $null) {
    $rc = Invoke-Orchestrator -ExtraArgs $orchArgs
    if ($rc -ne 0) {
        Write-Host "  FAIL: orchestrate_full_model.ps1 exited $rc" -ForegroundColor Red
        $step1OK = $false
    }
} else {
    # ConfigFile: iterate per UC
    $failedUcs = @()
    foreach ($uc in $ucList) {
        Write-Host "  → $uc" -ForegroundColor Gray
        $rc = Invoke-Orchestrator -ExtraArgs @("-UseCase", $uc)
        if ($rc -ne 0) { $failedUcs += $uc }
    }
    if ($failedUcs.Count -gt 0) {
        Write-Host "  FAIL: $($failedUcs -join ', ') failed orchestration" -ForegroundColor Red
        $step1OK = $false
    }
}

if ($step1OK) {
    Write-Host "  OK: TMDL and PBIP generated" -ForegroundColor Green
} else {
    Write-Host "  Pipeline aborted at Step 1. Fix orchestration errors and retry." -ForegroundColor Red
    exit 1
}

# ── Step 2: Desktop Readiness (ensure_pbip_desktop_ready.ps1) ─────────────────
Write-Host ""
Write-Host "── Step 2 / 4  PBIP Desktop Readiness ────────────────────" -ForegroundColor Cyan

$step2OK = $true
if ($SkipVerification) {
    Write-Host "  SKIPPED (--SkipVerification)" -ForegroundColor Yellow
} elseif ($DryRun) {
    Write-Host "  SKIPPED (DryRun)" -ForegroundColor Yellow
} elseif (-not (Test-Path (Join-Path $script:RepoRoot $desktopReadyScript))) {
    Write-Host "  WARN: ensure_pbip_desktop_ready.ps1 not found, skipping" -ForegroundColor Yellow
} else {
    & (Join-Path $script:RepoRoot $desktopReadyScript) -DistRoot $DistRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAIL: PBIP Desktop-readiness check failed" -ForegroundColor Red
        $step2OK = $false
    } else {
        Write-Host "  OK: All PBIP items are Desktop-ready" -ForegroundColor Green
    }
}

# ── Step 3: Page Structure (check_pbip_report_pages.ps1) ──────────────────────
Write-Host ""
Write-Host "── Step 3 / 4  Page Structure Verification ────────────────" -ForegroundColor Cyan

$step3OK = $true
if ($SkipVerification) {
    Write-Host "  SKIPPED (--SkipVerification)" -ForegroundColor Yellow
} elseif ($DryRun) {
    Write-Host "  SKIPPED (DryRun)" -ForegroundColor Yellow
} elseif (-not (Test-Path (Join-Path $script:RepoRoot $pageCheckScript))) {
    Write-Host "  WARN: check_pbip_report_pages.ps1 not found, skipping" -ForegroundColor Yellow
} else {
    & (Join-Path $script:RepoRoot $pageCheckScript) -DistRoot $DistRoot -UseCaseRoot $UseCaseRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAIL: Page structure check failed" -ForegroundColor Red
        $step3OK = $false
    } else {
        Write-Host "  OK: All report pages structurally valid" -ForegroundColor Green
    }
}

# ── Step 4: Template Compliance (check_page_template_compliance.py) ───────────
Write-Host ""
Write-Host "── Step 4 / 4  Page Template Compliance ───────────────────" -ForegroundColor Cyan

$step4OK = $true
if ($SkipCompliance -or $SkipVerification) {
    Write-Host "  SKIPPED" -ForegroundColor Yellow
} elseif ($DryRun) {
    Write-Host "  SKIPPED (DryRun)" -ForegroundColor Yellow
} elseif (-not (Test-Path (Join-Path $script:RepoRoot $complianceScript))) {
    Write-Host "  WARN: check_page_template_compliance.py not found, skipping" -ForegroundColor Yellow
} else {
    $pyArgs = @(
        (Join-Path $script:RepoRoot $complianceScript),
        "--dist-root", (Join-Path $script:RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)),
        "--use-case-root", (Join-Path $script:RepoRoot ($UseCaseRoot -replace '/', [IO.Path]::DirectorySeparatorChar))
    )
    python @pyArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAIL: Page template compliance check failed" -ForegroundColor Red
        $step4OK = $false
    } else {
        Write-Host "  OK: All pages comply with 3-30-300 template rules" -ForegroundColor Green
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
$elapsed   = [int]((Get-Date) - $startTime).TotalSeconds
$allPassed = $step1OK -and $step2OK -and $step3OK -and $step4OK

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Pipeline Summary  ($($elapsed)s)" -ForegroundColor Cyan
Write-Host "  Step 1 Generate:       $(if ($step1OK) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($step1OK) { 'Green' } else { 'Red' })
Write-Host "  Step 2 Desktop ready:  $(if ($SkipVerification -or $DryRun) { 'SKIP' } elseif ($step2OK) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($SkipVerification -or $DryRun) { 'Yellow' } elseif ($step2OK) { 'Green' } else { 'Red' })
Write-Host "  Step 3 Page structure: $(if ($SkipVerification -or $DryRun) { 'SKIP' } elseif ($step3OK) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($SkipVerification -or $DryRun) { 'Yellow' } elseif ($step3OK) { 'Green' } else { 'Red' })
Write-Host "  Step 4 Compliance:     $(if ($SkipCompliance -or $SkipVerification -or $DryRun) { 'SKIP' } elseif ($step4OK) { 'PASS' } else { 'FAIL' })" -ForegroundColor $(if ($SkipCompliance -or $SkipVerification -or $DryRun) { 'Yellow' } elseif ($step4OK) { 'Green' } else { 'Red' })
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Write pipeline manifest (non-critical — don't fail the pipeline on errors)
if (-not $DryRun) {
    try {
        $distAbsPath = Join-Path $script:RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (Test-Path $distAbsPath) {
            $manifest = @{
                generated_at   = (Get-Date -Format "o")
                scope          = $scopeLabel
                all_passed     = $allPassed
                steps          = @{
                    generate       = $step1OK
                    desktop_ready  = $step2OK
                    page_structure = $step3OK
                    compliance     = $step4OK
                }
                elapsed_seconds = $elapsed
            } | ConvertTo-Json -Depth 3
            $manifestPath = Join-Path $distAbsPath "pipeline_manifest.json"
            [System.IO.File]::WriteAllText($manifestPath, $manifest, (New-Object System.Text.UTF8Encoding $false))
        }
    } catch {
        Write-Verbose "Could not write pipeline_manifest.json: $($_.Exception.Message)"
    }
}

if ($allPassed) {
    Write-Host "  PIPELINE PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "  PIPELINE FAILED — see step failures above" -ForegroundColor Red
    exit 1
}
