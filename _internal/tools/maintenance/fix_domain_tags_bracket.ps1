#!/usr/bin/env pwsh
# Fix domain_tags to use bracket array syntax: domain_tag: [TagName]

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
$fixedCount = 0
$i = 0

while ($i -lt $lines.Count) {
    $line = $lines[$i]
    
    # Track current KPI ID
    if ($line -match '^\s*- kpi_id: (.+)') {
        $currentKpiId = $matches[1].Trim()
    }
    
    # Found domain_tag line without bracket format
    if ($line -match '^\s+(domain_tag:\s*)$' -and $currentKpiId) {
        $prefix = $currentKpiId.Split('.')[0]
        if ($domainMap.ContainsKey($prefix)) {
            $domain = $domainMap[$prefix]
            
            # Skip the next line if it's the list item "  - Domain"
            if (($i + 1) -lt $lines.Count -and $lines[$i + 1] -match '^\s+- ') {
                $i++  # Skip the old list format line
            }
            # Skip blank line if present
            if (($i + 1) -lt $lines.Count -and $lines[$i + 1] -match '^\s*$') {
                $i++  # Skip blank line
            }
            
            # Add the corrected line with bracket format
            $newLines += "  domain_tag: [$domain]"
            $fixedCount++
            Write-Host "  Fixed domain_tag for $currentKpiId to [$domain]" -ForegroundColor Green
        } else {
            $newLines += $line
        }
    } else {
        $newLines += $line
    }
    
    $i++
}

# Save
$content = $newLines -join "`r`n"
Set-Content -Path $catalogPath -Value $content -NoNewline

Write-Host "`nFixed $fixedCount domain_tags to bracket format" -ForegroundColor Cyan
