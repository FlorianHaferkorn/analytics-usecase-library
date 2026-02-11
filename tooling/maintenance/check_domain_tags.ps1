#!/usr/bin/env pwsh
# Check domain_tag coverage in KPI Catalog

$catalogPath = Join-Path $PSScriptRoot "..\..\..\core\kpi_catalog\KPI_Catalog.md"
$content = Get-Content -Path $catalogPath -Raw

# Find all kpi_ids
$kpiBlocks = [regex]::Matches($content, '(?ms)##\s+(\S+)\s+.*?(?=\n##\s+\S+|$)')
$totalKpis = $kpiBlocks.Count

# Find KPIs with domain_tags
$taggedKpis = [regex]::Matches($content, '(?ms)##\s+(\S+)\s+.*?domain_tag:\s*\n\s+-\s+[^\n]+')
$taggedCount = $taggedKpis.Count

Write-Host "`nDomain Tag Coverage:" -ForegroundColor Cyan
Write-Host "  Total KPIs: $totalKpis" -ForegroundColor White
Write-Host "  With domain_tags: $taggedCount" -ForegroundColor Green
Write-Host "  Missing domain_tags: $($totalKpis - $taggedCount)" -ForegroundColor Yellow

if ($taggedCount -lt $totalKpis) {
    Write-Host "`nFinding KPIs without domain_tags..." -ForegroundColor Yellow
    
    $taggedIds = $taggedKpis | ForEach-Object { $_.Groups[1].Value }
    $allIds = $kpiBlocks | ForEach-Object { $_.Groups[1].Value }
    $missingTagIds = $allIds | Where-Object { $_ -notin $taggedIds }
    
    Write-Host "`nKPIs missing domain_tags ($($missingTagIds.Count)):" -ForegroundColor Yellow
    $missingTagIds | ForEach-Object { Write-Host "  - $_" }
}
