#!/usr/bin/env pwsh
# Fix domain_tag issues in KPI Catalog

$catalogPath = Join-Path $PSScriptRoot "..\..\..\core\kpi_catalog\KPI_Catalog.md"
$content = Get-Content -Path $catalogPath -Raw

Write-Host "Fixing domain_tags..." -ForegroundColor Cyan

# Domain Mapping
$domainMap = @{
    'cost' = 'Finance'
    'crm' = 'Customer & Market'
    'enterprise' = 'Enterprise & Governance'
    'fin' = 'Finance'
    'hr' = 'People & Culture'
    'inv' = 'Supply Chain'
    'margin' = 'Finance'
    'ops' = 'Operations'
    'order' = 'Commercial'
    'people' = 'People & Culture'
    'plan' = 'Supply Chain'
    'plans' = 'Supply Chain'
    'profit' = 'Finance'
    'quality' = 'Operations'
    'res' = 'Operations'
    'sales' = 'Commercial'
    'scm' = 'Supply Chain'
    'shipments' = 'Supply Chain'
    'supply' = 'Supply Chain'
    'svc' = 'Service & Experience'
    'wc' = 'Finance'
}

$fixedCount = 0
$addedCount = 0

# Step 1: Remove duplicate domain_tags
$beforeDupes = $content
$pattern = '(?m)(  - [^\r\n]+)\r?\n\s*\1\r?\n'
$replacement = '$1' + "`r`n"
$content = $content -replace $pattern, $replacement
if ($content -ne $beforeDupes) {
    $dupesFixed = ([regex]::Matches($beforeDupes, '(?m)(  - [^\r\n]+)\r?\n\s*\1')).Count
    Write-Host "  Removed $dupesFixed duplicate domain_tag entries" -ForegroundColor Green
    $fixedCount += $dupesFixed
}

# Step 2: Add missing domain_tags
foreach ($prefix in $domainMap.Keys) {
    $domain = $domainMap[$prefix]
    
    # Pattern: Find KPIs with prefix where domain_tag: is followed by empty line or whitespace-only line, then use_case_ref
    # We look for: domain_tag:\n\n  use_case_ref OR domain_tag:\n  use_case_ref (without tag list)
    $pattern = "(?ms)(kpi_id: $prefix\.[^\r\n]+.*?domain_tag:\s*\r?\n)(\r?\n)?(\s*use_case_ref:)"
    
    while ($content -match $pattern) {
        # Check if there's already a tag (line starts with "  - ")
        $matchObj = [regex]::Match($content, $pattern)
        $before = $matchObj.Groups[1].Value
        $emptyLine = $matchObj.Groups[2].Value
        $useCase = $matchObj.Groups[3].Value
        
        # Only add if no tag exists (no line starting with "  - " between domain_tag and use_case_ref)
        if (-not ($before + $emptyLine -match '  - [^\r\n]+\r?\n$')) {
            $content = $content -replace $pattern, "`${1}  - $domain`r`n`${3}", 1
            $addedCount++
        } else {
            break  # Tag already exists, skip this prefix
        }
    }
    
    if ($addedCount -gt 0) {
        Write-Host "  + Added '$domain' tag to KPIs with prefix '$prefix'" -ForegroundColor Green
    }
}

# Save changes
Set-Content -Path $catalogPath -Value $content -NoNewline

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  Duplicates removed: $fixedCount" -ForegroundColor Green
Write-Host "  Domain tags added: $addedCount" -ForegroundColor Green
Write-Host "  Total fixes: $($fixedCount + $addedCount)" -ForegroundColor Cyan
