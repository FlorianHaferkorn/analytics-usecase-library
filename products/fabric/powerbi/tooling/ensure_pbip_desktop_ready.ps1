# ensure_pbip_desktop_ready.ps1
# Iterates over dist: auto-fixes missing definition.pbism (SemanticModel) and definition.pbir (Report),
# then re-validates until all checks pass or MaxIterations is reached.
# Run from repository root. Use after orchestration so Desktop can open Report + SemanticModel.

Param(
    [string]$DistRoot = "products/fabric/powerbi/dist",
    [int]$MaxIterations = 5,
    [string]$RepoRoot = $null,
    [switch]$CreateLegacyPbixProjArtifacts
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
$distPath = if ([System.IO.Path]::IsPathRooted($DistRoot)) {
    $DistRoot
} else {
    Join-Path $RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)
}
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
        } catch { Write-Verbose "Could not read report.json in ${ReportDir}: $($_.Exception.Message)" }
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

function Write-VersionTxtIfMissing {
    param([string]$ReportDir)

    $versionPath = Join-Path $ReportDir "Version.txt"
    if (Test-Path $versionPath) { return $false }

    [System.IO.File]::WriteAllText($versionPath, "1.25", $utf8NoBom)
    Write-Host "  Fixed: added $versionPath" -ForegroundColor Green
    return $true
}

function Write-JsonPlaceholderIfMissing {
    param(
        [string]$FilePath,
        [string]$Label
    )

    if (Test-Path $FilePath) { return $false }

    [System.IO.File]::WriteAllText($FilePath, "{}", $utf8NoBom)
    Write-Host "  Fixed: added $Label" -ForegroundColor Green
    return $true
}

function Remove-IfExists {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return $false }

    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    Write-Host "  Removed legacy artifact: $Path" -ForegroundColor Green
    return $true
}

function Sync-LegacyPbixProjReport {
    param([string]$ReportDir)

    $definitionDir = Join-Path $ReportDir "definition"
    $definitionReport = Join-Path $definitionDir "report.json"
    if (-not (Test-Path $definitionReport)) { return $false }

    $reportRoot = Join-Path $ReportDir "Report"
    $sectionsRoot = Join-Path $reportRoot "sections"
    New-Item -ItemType Directory -Force -Path $sectionsRoot | Out-Null

    $changed = $false
    $legacyReportPath = Join-Path $reportRoot "report.json"
    Copy-Item -Path $definitionReport -Destination $legacyReportPath -Force
    $changed = $true

    Get-ChildItem -Path $sectionsRoot -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    $pagesRoot = Join-Path $definitionDir "pages"
    if (-not (Test-Path $pagesRoot)) { return $changed }

    $pageOrder = @()
    $pagesMetaPath = Join-Path $pagesRoot "pages.json"
    if (Test-Path $pagesMetaPath) {
        try {
            $pagesMeta = Get-Content -Path $pagesMetaPath -Raw -ErrorAction Stop | ConvertFrom-Json
            $pageOrder = @($pagesMeta.pageOrder)
        } catch {
            $pageOrder = @()
        }
    }
    if ($pageOrder.Count -eq 0) {
        $pageOrder = @(Get-ChildItem -Path $pagesRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -ExpandProperty Name)
    }

    for ($index = 0; $index -lt $pageOrder.Count; $index++) {
        $pageId = $pageOrder[$index]
        $pageDir = Join-Path $pagesRoot $pageId
        $pageJsonPath = Join-Path $pageDir "page.json"
        if (-not (Test-Path $pageJsonPath)) { continue }

        try {
            $pageJson = Get-Content -Path $pageJsonPath -Raw -ErrorAction Stop | ConvertFrom-Json
            $displayName = if ($pageJson.displayName) { [string]$pageJson.displayName } elseif ($pageJson.name) { [string]$pageJson.name } else { [string]$pageId }
        } catch {
            $displayName = [string]$pageId
        }

        $safeDisplayName = ($displayName -replace '[<>:"/\\|?*]', '_')
        $sectionDir = Join-Path $sectionsRoot ("{0:D3}_{1}" -f $index, $safeDisplayName)
        $visualsDir = Join-Path $sectionDir "visualContainers"
        New-Item -ItemType Directory -Force -Path $visualsDir | Out-Null
        Copy-Item -Path $pageJsonPath -Destination (Join-Path $sectionDir "section.json") -Force

        $srcVisuals = Join-Path $pageDir "visuals"
        if (-not (Test-Path $srcVisuals)) { continue }

        Get-ChildItem -Path $srcVisuals -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $srcVisualJson = Join-Path $_.FullName "visual.json"
            if (-not (Test-Path $srcVisualJson)) { return }

            $legacyVisualDir = Join-Path $visualsDir $_.Name
            New-Item -ItemType Directory -Force -Path $legacyVisualDir | Out-Null
            Copy-Item -Path $srcVisualJson -Destination (Join-Path $legacyVisualDir "visualContainer.json") -Force
        }
    }

    Write-Host "  Fixed: synced legacy PbixProj Report folder in $ReportDir" -ForegroundColor Green
    return $changed
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
        if ($CreateLegacyPbixProjArtifacts) {
            if (Write-VersionTxtIfMissing -ReportDir $_.FullName) { $fixedAny = $true }
            if (Write-JsonPlaceholderIfMissing -FilePath (Join-Path $_.FullName "ReportMetadata.json") -Label (Join-Path $_.FullName "ReportMetadata.json")) { $fixedAny = $true }
            if (Write-JsonPlaceholderIfMissing -FilePath (Join-Path $_.FullName "ReportSettings.json") -Label (Join-Path $_.FullName "ReportSettings.json")) { $fixedAny = $true }
            if (Sync-LegacyPbixProjReport -ReportDir $_.FullName) { $fixedAny = $true }
        } else {
            if (Remove-IfExists -Path (Join-Path $_.FullName "Version.txt")) { $fixedAny = $true }
            if (Remove-IfExists -Path (Join-Path $_.FullName "ReportMetadata.json")) { $fixedAny = $true }
            if (Remove-IfExists -Path (Join-Path $_.FullName "ReportSettings.json")) { $fixedAny = $true }
            if (Remove-IfExists -Path (Join-Path $_.FullName "Report")) { $fixedAny = $true }
        }
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
