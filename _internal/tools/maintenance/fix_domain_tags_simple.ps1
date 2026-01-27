#!/usr/bin/env pwsh
# Simple and robust domain_tag fixer

$catalogPath = Join-Path $PSScriptRoot "..\..\..\framework\kpi_catalog\KPI_Catalog.md"
$lines = Get-Content -Path $catalogPath

# Domain Mapping
$domainMap = @{
    'cost' = 'Finance'; 'crm' = 'Customer & Market'; 'enterprise' = 'Enterprise & Governance';
    'fin' = 'Finance'; 'hr' = 'People & Culture'; 'inv' = 'Supply Chain'; 'margin' = 'Finance';
    'ops' = 'Operations'; 'order' = 'Commercial'; 'people' = 'People & Culture'; 'plan' = 'Supply Chain';
    'plans' = 'Supply Chain'; 'profit' = 'Finance'; 'quality' = 'Operations'; 'res' = 'Operations';
    'sales' = 'Commercial'; 'scm' = 'Supply Chain'; 'shipments' = 'Supply Chain'; 'supply' = 'Supply Chain';
    'svc' = 'Service & Experience'; 'wc' = 'Finance'
}

$newLines = @()
$currentKpiId = $null
$domainTagLineIndex = -1
$addedCount = 0

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    
    # Track current KPI ID
    if ($line -match '^\s*- kpi_id: (.+)') {
        $currentKpiId = $matches[1].Trim()
    }
    
    # Found domain_tag line
    if ($line -match '^\s+domain_tag:\s*$') {
        $domainTagLineIndex = $i
        $newLines += $line
        
        # Check next line: if it's empty or use_case_ref, we need to add tag
        if (($i + 1) -lt $lines.Count) {
            $nextLine = $lines[$i + 1]
            
            # If next line is NOT a tag (doesn't start with "  - "), add the tag
            if ($nextLine -notmatch '^\s+- \S' -and $currentKpiId) {
                $prefix = $currentKpiId.Split('.')[0]
                if ($domainMap.ContainsKey($prefix)) {
                    $domain = $domainMap[$prefix]
                    $newLines += "  - $domain"
                    $addedCount++
                    Write-Host "  + Added '$domain' to $currentKpiId" -ForegroundColor Green
                }
            }
        }
        continue
    }
    
    $newLines += $line
}

# Save with proper line endings
$content = $newLines -join "`r`n"
Set-Content -Path $catalogPath -Value $content -NoNewline

Write-Host "`nAdded $addedCount domain_tags" -ForegroundColor Cyan
