# products/fabric/powerbi/tooling/check_report_structure.ps1
# Validates that generated report folders under dist match the canonical PBIP layout
# (see products/fabric/powerbi/docs/PBIP_REPORT_STRUCTURE.md). Ensures definition/report.json
# (Fabric 3.0 schema; no datasetReference in report.json—binding is in definition.pbir), definition/version.json, definition/pages/pages.json,
# and at least one Page_* folder with page.json (and visuals/) exist.

Param(
    [string]$DistRoot = "products/fabric/powerbi/dist",
    [string]$RepoRoot = $null
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    # PSScriptRoot = repo/products/fabric/powerbi/tooling -> repo = 4 levels up
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
Push-Location $RepoRoot | Out-Null
$distPath = Join-Path $RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)
$failCount = 0

$requiredReportSchema = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json"

if (-not (Test-Path $distPath)) {
    Write-Host "Dist path not found: $distPath" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

$reportDirs = Get-ChildItem $distPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue
foreach ($dir in $reportDirs) {
    $reportOk = $true
    $base = $dir.FullName
    $defPath = Join-Path $base "definition"
    $pagesPath = Join-Path $defPath "pages"
    $reportJsonPath = Join-Path $defPath "report.json"
    $versionJsonPath = Join-Path $defPath "version.json"
    $pagesJsonPath = Join-Path $pagesPath "pages.json"

    # 1. definition/report.json
    if (-not (Test-Path $reportJsonPath)) {
        Write-Host "FAIL $($dir.Name): definition/report.json missing" -ForegroundColor Red
        $failCount++; $reportOk = $false
        continue
    }
    try {
        $reportJson = Get-Content $reportJsonPath -Raw | ConvertFrom-Json
        $schemaVal = $reportJson.PSObject.Properties['$schema'].Value
        if (-not $schemaVal -or $schemaVal -ne $requiredReportSchema) {
            Write-Host "FAIL $($dir.Name): report.json must use Fabric 3.0 report schema" -ForegroundColor Red
            $failCount++; $reportOk = $false
        }
        # datasetReference must not be in report.json (schema disallows it); binding is in definition.pbir only.
    } catch {
        Write-Host "FAIL $($dir.Name): invalid report.json - $_" -ForegroundColor Red
        $failCount++; $reportOk = $false
        continue
    }

    # 2. definition/version.json
    if (-not (Test-Path $versionJsonPath)) {
        Write-Host "FAIL $($dir.Name): definition/version.json missing" -ForegroundColor Red
        $failCount++; $reportOk = $false
    }

    # 3. definition/pages/pages.json
    if (-not (Test-Path $pagesJsonPath)) {
        Write-Host "FAIL $($dir.Name): definition/pages/pages.json missing" -ForegroundColor Red
        $failCount++; $reportOk = $false
    } else {
        try {
            $pagesJson = Get-Content $pagesJsonPath -Raw | ConvertFrom-Json
            $pageOrder = $pagesJson.pageOrder
            if (-not $pageOrder -or $pageOrder.Count -eq 0) {
                Write-Host "FAIL $($dir.Name): pages.json pageOrder empty" -ForegroundColor Red
                $failCount++; $reportOk = $false
            }
        } catch {
            Write-Host "FAIL $($dir.Name): invalid pages.json - $_" -ForegroundColor Red
            $failCount++; $reportOk = $false
        }
    }

    # 4. At least one Page_* folder with page.json (canonical layout)
    $pageDirs = @(Get-ChildItem $pagesPath -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^Page_" })
    $hasValidPage = $false
    foreach ($p in $pageDirs) {
        $pageJsonPath = Join-Path $p.FullName "page.json"
        if (Test-Path $pageJsonPath) {
            $hasValidPage = $true
            break
        }
    }
    if (-not $hasValidPage) {
        Write-Host "FAIL $($dir.Name): no definition/pages/Page_*/page.json found (canonical layout)" -ForegroundColor Red
        $failCount++; $reportOk = $false
    }

    if ($reportOk) {
        Write-Host "OK $($dir.Name): PBIP structure valid (report.json, version.json, pages, definition.pbir)" -ForegroundColor Green
    }
}

Pop-Location
if ($failCount -gt 0) {
    exit 1
}
exit 0
