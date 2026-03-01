# products/fabric/powerbi/orchestrator/measure_ops.ps1

Param(
    [ValidateSet("Import","List","Get")]
    [string]$Operation = "List",
    [string]$ConnectionName = "local_pbip",
    [string]$MeasuresFile,
    [string]$MeasureName
)

$ErrorActionPreference = "Stop"

# =========================================
# Helper: Load Connection
# =========================================
function Get-Connection {
    param([string]$Name)
    
    $connFile = Join-Path $PSScriptRoot "connections.json"
    if (-not (Test-Path $connFile)) {
        throw "Connection file not found: $connFile"
    }
    
    $connections = Get-Content $connFile -Raw | ConvertFrom-Json
    return $connections.$Name
}

# =========================================
# Helper: Parse Measures from TMDL
# =========================================
function Get-MeasuresFromTMDL {
    param([string]$TmdlPath)
    
    if (-not (Test-Path $TmdlPath)) {
        throw "TMDL file not found: $TmdlPath"
    }
    
    $content = Get-Content $TmdlPath -Raw
    
    # Parse measure blocks
    # Pattern: /// description\n  measure 'Name' = expression
    $measurePattern = '(?ms)///\s*(.+?)\s*\n\s*measure\s+[''"]([^''"]+)[''"](\s*=\s*(.+?))?(?=\s*(?:///|measure|$))'
    
    $measures = @()
    $matches = [regex]::Matches($content, $measurePattern)
    
    foreach ($match in $matches) {
        $measures += @{
            description = $match.Groups[1].Value.Trim()
            name = $match.Groups[2].Value
            expression = $match.Groups[4].Value.Trim()
        }
    }
    
    return $measures
}

# =========================================
# Main Operations
# =========================================

$conn = Get-Connection -Name $ConnectionName

switch ($Operation) {
    "Import" {
        if (-not $MeasuresFile) {
            throw "-MeasuresFile required for Import operation"
        }
        
        Write-Host "Importing measures from: $MeasuresFile" -ForegroundColor Gray
        
        if (-not (Test-Path $MeasuresFile)) {
            throw "Measures file not found: $MeasuresFile"
        }
        
        # Target path
        $targetPath = "$($conn.definitionPath)\tables\_Measures.tmdl"
        
        # Copy file
        Copy-Item $MeasuresFile $targetPath -Force
        
        # Parse to show summary
        $measures = Get-MeasuresFromTMDL -TmdlPath $targetPath
        
        Write-Host "  Imported $($measures.Count) measures to $targetPath" -ForegroundColor Green
        
        # Show first 5
        if ($measures.Count -gt 0) {
            Write-Host "`nFirst 5 measures:" -ForegroundColor Cyan
            $measures | Select-Object -First 5 | ForEach-Object {
                Write-Host "  - $($_.name)" -ForegroundColor Gray
                Write-Host "    $($_.description)" -ForegroundColor DarkGray
            }
        }
    }
    
    "List" {
        $measuresPath = "$($conn.definitionPath)\tables\_Measures.tmdl"
        
        if (-not (Test-Path $measuresPath)) {
            Write-Host "No _Measures.tmdl file found" -ForegroundColor Yellow
            return @()
        }
        
        $measures = Get-MeasuresFromTMDL -TmdlPath $measuresPath
        
        Write-Host "Measures in model: $($measures.Count)" -ForegroundColor Cyan
        $measures | ForEach-Object {
            Write-Host "  - $($_.name)" -ForegroundColor Gray
        }
        
        return $measures
    }
    
    "Get" {
        if (-not $MeasureName) {
            throw "-MeasureName required for Get operation"
        }
        
        $measuresPath = "$($conn.definitionPath)\tables\_Measures.tmdl"
        
        if (-not (Test-Path $measuresPath)) {
            throw "No _Measures.tmdl file found"
        }
        
        $measures = Get-MeasuresFromTMDL -TmdlPath $measuresPath
        $measure = $measures | Where-Object { $_.name -eq $MeasureName }
        
        if (-not $measure) {
            throw "Measure '$MeasureName' not found"
        }
        
        Write-Host "Measure: $($measure.name)" -ForegroundColor Cyan
        Write-Host "Description: $($measure.description)" -ForegroundColor Gray
        Write-Host "Expression:" -ForegroundColor Gray
        Write-Host $measure.expression -ForegroundColor DarkGray
        
        return $measure
    }
    
    default {
        Write-Host "Operation '$Operation' not yet implemented" -ForegroundColor Yellow
        Write-Host "Available: Import, List, Get" -ForegroundColor Gray
    }
}
