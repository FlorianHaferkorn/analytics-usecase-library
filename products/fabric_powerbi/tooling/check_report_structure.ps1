# products/fabric_powerbi/tooling/check_report_structure.ps1
# Validates that generated report folders under dist have definition/report.json and datasetReference set.
# Optional verification step; no Power BI Desktop automation.

Param(
    [string]$DistRoot = "products/fabric_powerbi/dist",
    [string]$RepoRoot = $null
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) {
    # PSScriptRoot = repo/products/fabric_powerbi/tooling -> repo = 4 levels up
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
Push-Location $RepoRoot | Out-Null
$distPath = Join-Path $RepoRoot ($DistRoot -replace '/', [IO.Path]::DirectorySeparatorChar)
$failCount = 0

if (-not (Test-Path $distPath)) {
    Write-Host "Dist path not found: $distPath" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

$reportDirs = Get-ChildItem $distPath -Directory -Filter "*.Report" -ErrorAction SilentlyContinue
foreach ($dir in $reportDirs) {
    $reportJson = Join-Path $dir.FullName "definition\report.json"
    if (-not (Test-Path $reportJson)) {
        Write-Host "FAIL $($dir.Name): definition/report.json missing" -ForegroundColor Red
        $failCount++
        continue
    }
    try {
        $json = Get-Content $reportJson -Raw | ConvertFrom-Json
        $ref = $json.datasetReference
        if (-not $ref -or (-not $ref.byPath -and -not $ref.datasetId)) {
            Write-Host "FAIL $($dir.Name): datasetReference missing or empty" -ForegroundColor Red
            $failCount++
        } else {
            Write-Host "OK $($dir.Name): report.json present, datasetReference set" -ForegroundColor Green
        }
    } catch {
        Write-Host "FAIL $($dir.Name): invalid report.json - $_" -ForegroundColor Red
        $failCount++
    }
}

Pop-Location
if ($failCount -gt 0) {
    exit 1
}
exit 0
