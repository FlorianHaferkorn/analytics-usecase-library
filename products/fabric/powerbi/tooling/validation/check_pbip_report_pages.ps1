# check_pbip_report_pages.ps1
# Verifies that every .Report in dist/ has the expected 2-page structure with required visual slots.
#
# Checks per report:
#   - definition.pbir exists and is valid JSON
#   - definition/pages/ exists with pages.json
#   - Exactly 2 page subdirectories (Overview + Detail)
#   - Overview page has visuals: KPI_Cards, at least one Main_N, Slicer_Date
#   - Detail page has visuals: Detail_Matrix, Slicer_Pane
#   - If UseCase_Bracket.yaml action_panel: true -> ActionPanel visual must be present on Detail page
#
# Exit codes: 0 = all pass, 1 = violations, 2 = unexpected error.
# Run from repository root.

Param(
    [string]$DistRoot      = "products/fabric/powerbi/dist",
    [string]$UseCaseRoot   = "core\usecases\core",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

$script:RepoRoot = $PSScriptRoot
while ($script:RepoRoot) {
    if ((Test-Path (Join-Path $script:RepoRoot "core")) -and (Test-Path (Join-Path $script:RepoRoot "tooling"))) { break }
    $script:RepoRoot = Split-Path -Parent $script:RepoRoot
}
if (-not $script:RepoRoot) { throw "Repo root not found" }

$distAbs    = if ([IO.Path]::IsPathRooted($DistRoot))    { $DistRoot }    else { Join-Path $script:RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar) }
$ucRootAbs  = if ([IO.Path]::IsPathRooted($UseCaseRoot)) { $UseCaseRoot } else { Join-Path $script:RepoRoot ($UseCaseRoot -replace '/', [IO.Path]::DirectorySeparatorChar) }

if (-not (Test-Path $distAbs)) {
    Write-Host "WARN: dist path not found: $distAbs - nothing to check." -ForegroundColor Yellow
    exit 0
}

# Helpers

function Get-BracketActionPanel {
    # Returns $true if the use case bracket declares action_panel: true on any 300s component.
    param([string]$UcId)
    if (-not (Test-Path $ucRootAbs)) { return $false }
    $dir = Get-ChildItem $ucRootAbs -Directory -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -like "$UcId*" } | Select-Object -First 1
    if (-not $dir) { return $false }
    $bracketPath = Join-Path $dir.FullName "UseCase_Bracket.yaml"
    if (-not (Test-Path $bracketPath)) { return $false }
    $raw = Get-Content -Raw $bracketPath
    return ($raw -match "action_panel\s*:\s*true")
}

function Get-VisualType {
    param([string]$VisualJsonPath)
    try {
        $obj = Get-Content -Raw $VisualJsonPath | ConvertFrom-Json
        return $obj.visual.visualType
    } catch { return $null }
}

function Test-PageHasVisual {
    param([string]$PageDir, [string]$VisualName)
    return (Test-Path (Join-Path $PageDir "visuals\$VisualName\visual.json"))
}

function Test-PageHasAnyMainVisual {
    param([string]$PageDir)
    $visuDir = Join-Path $PageDir "visuals"
    if (-not (Test-Path $visuDir)) { return $false }
    return ($null -ne (Get-ChildItem $visuDir -Directory -ErrorAction SilentlyContinue |
                       Where-Object { $_.Name -match '^Main_\d+$' } | Select-Object -First 1))
}

# Main scan

$reports = @(Get-ChildItem $distAbs -Directory -Filter "*.Report" -ErrorAction SilentlyContinue)

if ($reports.Count -eq 0) {
    Write-Host "No .Report directories found in $distAbs." -ForegroundColor Yellow
    exit 0
}

Write-Host "Checking $($reports.Count) report(s) in $distAbs..." -ForegroundColor Cyan

$violations  = [System.Collections.Generic.List[string]]::new()
$passedCount = 0

foreach ($report in $reports) {
    $reportName = $report.Name
    $ucId = if ($reportName -match '^([A-Z]{2,3}-\d+)') { $Matches[1] } else { $null }
    $errs = [System.Collections.Generic.List[string]]::new()

    # 1. definition.pbir
    $pbirPath = Join-Path $report.FullName "definition.pbir"
    if (-not (Test-Path $pbirPath)) {
        $errs.Add("Missing definition.pbir")
    } else {
        try { Get-Content -Raw $pbirPath | ConvertFrom-Json | Out-Null }
        catch { $errs.Add("definition.pbir is not valid JSON: $($_.Exception.Message)") }
    }

    # 2. pages/ + pages.json
    $pagesDir      = Join-Path $report.FullName "definition\pages"
    $pagesJsonPath = Join-Path $pagesDir "pages.json"
    if (-not (Test-Path $pagesDir)) {
        $errs.Add("Missing definition/pages/")
    } elseif (-not (Test-Path $pagesJsonPath)) {
        $errs.Add("Missing definition/pages/pages.json")
    }

    # 3. Exactly 2 page subdirectories
    $pageDirs = @()
    if (Test-Path $pagesDir) {
        $pageDirs = @(Get-ChildItem $pagesDir -Directory -ErrorAction SilentlyContinue)
    }
    if ($pageDirs.Count -ne 2) {
        $errs.Add("Expected 2 page directories (Overview + Detail), found $($pageDirs.Count): $($pageDirs.Name -join ', ')")
    }

    # 4. Identify Overview and Detail pages
    $overviewDir = $pageDirs | Where-Object { $_.Name -match 'Overview' } | Select-Object -First 1
    $detailDir   = $pageDirs | Where-Object { $_.Name -match 'Detail' }   | Select-Object -First 1

    if (-not $overviewDir -and $pageDirs.Count -gt 0) {
        $overviewDir = $pageDirs[0]
        $errs.Add("No page directory contains 'Overview' in its name; treating '$($overviewDir.Name)' as overview")
    }
    if (-not $detailDir -and $pageDirs.Count -gt 1) {
        $detailDir = $pageDirs[1]
        $errs.Add("No page directory contains 'Detail' in its name; treating '$($detailDir.Name)' as detail")
    }

    # 5. Overview page visual slots
    if ($overviewDir) {
        if (-not (Test-PageHasVisual -PageDir $overviewDir.FullName -VisualName "KPI_Cards")) {
            $errs.Add("Overview '$($overviewDir.Name)': missing KPI_Cards visual slot")
        }
        if (-not (Test-PageHasAnyMainVisual -PageDir $overviewDir.FullName)) {
            $errs.Add("Overview '$($overviewDir.Name)': no Main_N visual slot found (expected Main_1 at minimum)")
        }
        if (-not (Test-PageHasVisual -PageDir $overviewDir.FullName -VisualName "Slicer_Date")) {
            $errs.Add("Overview '$($overviewDir.Name)': missing Slicer_Date visual slot")
        }
    }

    # 6. Detail page visual slots
    if ($detailDir) {
        if (-not (Test-PageHasVisual -PageDir $detailDir.FullName -VisualName "Detail_Matrix")) {
            $errs.Add("Detail '$($detailDir.Name)': missing Detail_Matrix visual slot")
        }
        if (-not (Test-PageHasVisual -PageDir $detailDir.FullName -VisualName "Slicer_Pane")) {
            $errs.Add("Detail '$($detailDir.Name)': missing Slicer_Pane visual slot")
        }

        # 7. ActionPanel: required if bracket says action_panel: true
        if ($ucId) {
            $needsActionPanel = Get-BracketActionPanel -UcId $ucId
            if ($needsActionPanel -and -not (Test-PageHasVisual -PageDir $detailDir.FullName -VisualName "ActionPanel")) {
                $errs.Add("Detail '$($detailDir.Name)': UseCase_Bracket.yaml sets action_panel: true but ActionPanel visual slot is missing")
            }
        }
    }

    # 8. page.json name/displayName must match folder and use case ID
    foreach ($pageDir in $pageDirs) {
        $pageJsonPath = Join-Path $pageDir.FullName "page.json"
        if (-not (Test-Path $pageJsonPath)) { continue }
        try {
            $pageObj = Get-Content -Raw $pageJsonPath | ConvertFrom-Json
        } catch {
            $errs.Add("Page '$($pageDir.Name)': page.json is not valid JSON")
            continue
        }
        if ($pageObj.name -ne $pageDir.Name) {
            $errs.Add("Page '$($pageDir.Name)': page.json name '$($pageObj.name)' does not match folder name")
        }
        if ($ucId -and $pageObj.displayName -and ($pageObj.displayName -notmatch [regex]::Escape($ucId))) {
            $errs.Add("Page '$($pageDir.Name)': displayName '$($pageObj.displayName)' does not reference use case $ucId")
        }
    }

    if (Test-Path $pagesJsonPath) {
        try {
            $pagesMeta = Get-Content -Raw $pagesJsonPath | ConvertFrom-Json
            $order = @($pagesMeta.pageOrder)
            foreach ($entry in $order) {
                $expectedDir = Join-Path $pagesDir $entry
                if (-not (Test-Path $expectedDir)) {
                    $errs.Add("pages.json pageOrder references '$entry' but no matching page directory exists")
                }
            }
            foreach ($pageDir in $pageDirs) {
                $pj = Join-Path $pageDir.FullName "page.json"
                if (-not (Test-Path $pj)) { continue }
                $pageObj = Get-Content -Raw $pj | ConvertFrom-Json
                if ($order -contains $pageDir.Name -and $pageObj.name -ne $pageDir.Name) {
                    $errs.Add("pages.json lists '$($pageDir.Name)' but its page.json name is '$($pageObj.name)'")
                }
            }
        } catch {
            $errs.Add("pages.json is not valid JSON: $($_.Exception.Message)")
        }
    }

    # Report per report
    if ($errs.Count -gt 0) {
        Write-Host "  FAIL  $reportName" -ForegroundColor Red
        foreach ($e in $errs) {
            Write-Host "        - $e" -ForegroundColor Red
            $violations.Add("[$reportName] $e")
        }
    } else {
        if ($Verbose) { Write-Host "  PASS  $reportName" -ForegroundColor Green }
        $passedCount++
    }
}

Write-Host ""
if ($violations.Count -eq 0) {
    Write-Host "Page structure check: PASSED ($($reports.Count) report(s))" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Page structure check: FAILED - $($violations.Count) violation(s) across $($reports.Count - $passedCount) report(s)" -ForegroundColor Red
    exit 1
}
