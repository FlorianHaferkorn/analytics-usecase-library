# ensure_pbip_desktop_ready.ps1
# Iterates over dist: auto-fixes missing definition.pbism (SemanticModel) and definition.pbir (Report),
# then re-validates until all checks pass or MaxIterations is reached.
# Run from repository root. Use after orchestration so Desktop can open Report + SemanticModel.

Param(
    [string]$DistRoot = "products/fabric/powerbi/dist",
    [int]$MaxIterations = 5,
    [string]$RepoRoot = $null
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
$distPath = Join-Path $RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# Fix .pbip files that are missing $schema (Desktop Feb 2026+ requires pbipProperties schema)
function Ensure-PbipSchema {
    param([string]$distFullPath)
    $changed = $false
    $pbipSchema = "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
    Get-ChildItem -Path $distFullPath -Recurse -Filter "*.pbip" -File -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $content = [System.IO.File]::ReadAllText($_.FullName)
            $obj = $content | ConvertFrom-Json
            if (-not $obj.PSObject.Properties['$schema']) {
                $obj | Add-Member -NotePropertyName '$schema' -NotePropertyValue $pbipSchema -Force
                $newJson = $obj | ConvertTo-Json -Depth 5 -Compress
                [System.IO.File]::WriteAllText($_.FullName, $newJson, $utf8NoBom)
                Write-Host "  Fixed: added `$schema to $($_.Name)" -ForegroundColor Green
                $changed = $true
            }
        } catch { Write-Verbose "Skipped $($_.FullName): $($_.Exception.Message)" }
    }
    return $changed
}

function Write-PbismIfMissing {
    param([string]$ModelDir)
    $pbismPath = Join-Path $ModelDir "definition.pbism"
    if (Test-Path $pbismPath) { return $false }
    $json = @{
        '$schema' = "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json"
        version   = "4.2"
        settings  = @{}
    } | ConvertTo-Json -Depth 3
    [System.IO.File]::WriteAllText($pbismPath, $json, $utf8NoBom)
    Write-Host "  Fixed: added $pbismPath" -ForegroundColor Green
    return $true
}

function Write-PbirIfMissingOrWrong {
    param([string]$ReportDir)
    $pbirPath = Join-Path $ReportDir "definition.pbir"
    $reportJsonPath = Join-Path $ReportDir "definition\report.json"
    $datasetPath = $null
    if (Test-Path $reportJsonPath) {
        try {
            $rj = Get-Content -Raw -Path $reportJsonPath | ConvertFrom-Json
            if ($rj.datasetReference -and $rj.datasetReference.byPath -and $rj.datasetReference.byPath.path) {
                $datasetPath = $rj.datasetReference.byPath.path -replace '\\', '/'
            }
        } catch { Write-Verbose "Could not read report.json in $ReportDir: $($_.Exception.Message)" }
    }
    $needsWrite = $false
    if (-not (Test-Path $pbirPath)) {
        $needsWrite = $true
    } else {
        try {
            $dp = Get-Content -Raw -Path $pbirPath | ConvertFrom-Json
            if (-not $datasetPath -and $dp.datasetReference -and $dp.datasetReference.byPath -and $dp.datasetReference.byPath.path) {
                $datasetPath = $dp.datasetReference.byPath.path -replace '\\', '/'
            }
            $schema = $dp.PSObject.Properties['$schema'].Value
            if ($schema -notmatch 'definitionProperties/(1|2)\.\d+\.\d+/schema\.json$') {
                $needsWrite = $true
            }
        } catch { $needsWrite = $true }
    }
    if (-not $needsWrite) { return $false }
    $pbirData = @{
        '$schema'         = "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json"
        version           = "4.0"
        datasetReference  = if ($datasetPath) { @{ byPath = @{ path = $datasetPath } } } else { @{} }
    }
    if (-not $datasetPath) { $pbirData.Remove('datasetReference') }
    $json = $pbirData | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($pbirPath, $json, $utf8NoBom)
    Write-Host "  Fixed: added/updated $pbirPath" -ForegroundColor Green
    return $true
}

function Test-DistValidation {
    param([string]$distFullPath)
    $hasErrors = $false
    # SemanticModel: must have definition.pbism
    Get-ChildItem -Path $distFullPath -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue | ForEach-Object {
        $pbism = Join-Path $_.FullName "definition.pbism"
        if (-not (Test-Path $pbism)) {
            Write-Host "  Validation FAIL: $($_.Name) missing definition.pbism" -ForegroundColor Red
            $hasErrors = $true
        }
    }
    # Report: run validate_pbip per report folder
    $validatePbip = Join-Path $RepoRoot "tooling\validation\pbip\validate_pbip.ps1"
    if (Test-Path $validatePbip) {
        Get-ChildItem -Path $distFullPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | ForEach-Object {
            & $validatePbip -Root $_.FullName 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 2) {
                Write-Host "  Validation FAIL: $($_.Name) (validate_pbip)" -ForegroundColor Red
                $hasErrors = $true
            }
        }
    } else {
        # Fallback: only check definition.pbir exists for reports
        Get-ChildItem -Path $distFullPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | ForEach-Object {
            $pbir = Join-Path $_.FullName "definition.pbir"
            if (-not (Test-Path $pbir)) {
                Write-Host "  Validation FAIL: $($_.Name) missing definition.pbir" -ForegroundColor Red
                $hasErrors = $true
            }
        }
    }
    return -not $hasErrors
}

# Main loop
if (-not (Test-Path $distPath)) {
    Write-Host "Dist path not found: $distPath" -ForegroundColor Red
    exit 2
}

Write-Host "PBIP Desktop readiness: fix and validate loop (max $MaxIterations iterations) at $distPath" -ForegroundColor Cyan
$iteration = 0
$fixedAny = $true
while ($iteration -lt $MaxIterations -and $fixedAny) {
    $iteration++
    Write-Host "`n--- Iteration $iteration ---" -ForegroundColor Cyan
    $fixedAny = $false
    # Fix: .pbip files missing $schema
    if (Ensure-PbipSchema -distFullPath $distPath) { $fixedAny = $true }
    # Fix: SemanticModel definition.pbism
    Get-ChildItem -Path $distPath -Directory -Filter "*.SemanticModel" -ErrorAction SilentlyContinue | ForEach-Object {
        if (Write-PbismIfMissing -ModelDir $_.FullName) { $fixedAny = $true }
    }
    # Fix: Report definition.pbir
    Get-ChildItem -Path $distPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue | ForEach-Object {
        if (Write-PbirIfMissingOrWrong -ReportDir $_.FullName) { $fixedAny = $true }
    }
    # Validate (run validate_pbip per report; checks may still fail for other reasons)
    $allPass = Test-DistValidation -distFullPath $distPath
    if ($allPass) {
        Write-Host "`nAll PBIP Desktop checks passed." -ForegroundColor Green
        exit 0
    }
    if (-not $fixedAny) {
        Write-Host "`nNo fixable issues; some validation errors remain. Fix manually and re-run." -ForegroundColor Yellow
        exit 1
    }
}
if ($iteration -ge $MaxIterations) {
    Write-Host "`nMax iterations ($MaxIterations) reached. Re-run to continue fixing or fix remaining errors manually." -ForegroundColor Yellow
    exit 1
}
exit 0
