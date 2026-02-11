# tooling/powerbi_mcp/relationship_ops.ps1

Param(
    [ValidateSet("Create","List","AutoDetect","CreateFromFactsheet")]
    [string]$Operation = "List",
    [string]$ConnectionName = "local_pbip",
    [string]$FactsheetPath,
    [hashtable]$RelationshipDefinition
)

$ErrorActionPreference = "Stop"

# =========================================
# Helper: Load Connection
# =========================================
function Get-Connection {
    param([string]$Name)
    
    $connFile = "tooling/powerbi_mcp/connections.json"
    if (-not (Test-Path $connFile)) {
        throw "Connection file not found: $connFile"
    }
    
    $connections = Get-Content $connFile -Raw | ConvertFrom-Json
    return $connections.$Name
}

# =========================================
# Helper: Parse Relationships from Technical Factsheet
# =========================================
function Get-RelationshipsFromFactsheet {
    param([string]$FactsheetPath)
    
    if (-not (Test-Path $FactsheetPath)) {
        throw "Factsheet not found: $FactsheetPath"
    }
    
    $content = Get-Content $FactsheetPath -Raw
    
    # Parse section 4.2 Relationships
    $relPattern = '(?ms)###\s*4\.2\s+Relationships.*?```(?:yaml)?\s*(.*?)\s*```'
    $relMatch = [regex]::Match($content, $relPattern)
    
    if (-not $relMatch.Success) {
        Write-Host "  No relationships section found in factsheet" -ForegroundColor Yellow
        return @()
    }
    
    # Simple YAML parsing for relationships
    $yamlBlock = $relMatch.Groups[1].Value
    $relationships = @()
    
    # Parse format: "- from: fact_sales.OrgKey -> to: dim_org.OrgKey"
    $relLines = $yamlBlock -split "`n" | Where-Object { $_ -match 'from:.*to:' }
    
    foreach ($line in $relLines) {
        if ($line -match 'from:\s*(\w+)\.(\w+)\s*->\s*to:\s*(\w+)\.(\w+)') {
            $relationships += @{
                fromTable = $matches[1]
                fromColumn = $matches[2]
                toTable = $matches[3]
                toColumn = $matches[4]
                crossFilteringBehavior = "OneDirection"  # Default
                cardinality = "ManyToOne"  # Default for FK -> PK
            }
        }
    }
    
    return $relationships
}

# =========================================
# Helper: Auto-Detect Relationships based on naming convention
# =========================================
function Get-AutoDetectedRelationships {
    param([string]$DefinitionPath)
    
    $relationships = @()
    $tablesDir = "$DefinitionPath\tables"
    
    if (-not (Test-Path $tablesDir)) {
        return @()
    }
    
    # Get all tables
    $tableFiles = Get-ChildItem $tablesDir -Filter "*.tmdl"
    $tables = @{}
    
    foreach ($file in $tableFiles) {
        $content = Get-Content $file.FullName -Raw
        $tableName = $file.BaseName
        
        # Extract columns with *Key suffix
        $keyColumns = [regex]::Matches($content, 'column\s+(\w+Key)\s') | ForEach-Object { $_.Groups[1].Value }
        
        $tables[$tableName] = @{
            columns = $keyColumns
            isFact = ($tableName -match '^fact_')
            isDim = ($tableName -match '^dim_')
        }
    }
    
    # Auto-detect: fact_*.XyzKey -> dim_xyz.XyzKey
    foreach ($table in $tables.Keys) {
        if ($tables[$table].isFact) {
            foreach ($col in $tables[$table].columns) {
                # Try to find matching dimension
                $dimName = "dim_" + ($col -replace 'Key$', '').ToLower()
                
                if ($tables[$dimName]) {
                    $relationships += @{
                        fromTable = $table
                        fromColumn = $col
                        toTable = $dimName
                        toColumn = $col
                        crossFilteringBehavior = "OneDirection"
                        cardinality = "ManyToOne"
                        isAutoDetected = $true
                    }
                }
            }
        }
    }
    
    return $relationships
}

# =========================================
# Main Operations
# =========================================

$conn = Get-Connection -Name $ConnectionName

switch ($Operation) {
    "CreateFromFactsheet" {
        if (-not $FactsheetPath) {
            throw "-FactsheetPath required for CreateFromFactsheet operation"
        }
        
        Write-Host "Parsing relationships from: $FactsheetPath" -ForegroundColor Gray
        $relationships = Get-RelationshipsFromFactsheet -FactsheetPath $FactsheetPath
        
        if ($relationships.Count -eq 0) {
            Write-Host "  No relationships found" -ForegroundColor Yellow
            return
        }
        
        Write-Host "Found $($relationships.Count) relationships" -ForegroundColor Cyan
        
        foreach ($rel in $relationships) {
            Write-Host "  $($rel.fromTable).$($rel.fromColumn) -> $($rel.toTable).$($rel.toColumn)" -ForegroundColor Gray
            
            # TODO: Call Power BI MCP relationship_operations
            # For now: Generate TMDL file
            $relName = "$($rel.fromTable)_$($rel.toTable)"
            $tmdlPath = "$($conn.definitionPath)\relationships\$relName.tmdl"
            
            New-Item -ItemType Directory -Path "$($conn.definitionPath)\relationships" -Force -ErrorAction SilentlyContinue | Out-Null
            
            $tmdlContent = "relationship $relName`r`n"
            $tmdlContent += "  fromColumn: $($rel.fromTable).$($rel.fromColumn)`r`n"
            $tmdlContent += "  toColumn: $($rel.toTable).$($rel.toColumn)`r`n"
            $tmdlContent += "  cardinality: $($rel.cardinality)`r`n"
            $tmdlContent += "  crossFilteringBehavior: $($rel.crossFilteringBehavior)`r`n"
            
            $utf8 = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($tmdlPath, $tmdlContent, $utf8)
            
            Write-Host "    Created: $tmdlPath" -ForegroundColor Green
        }
    }
    
    "AutoDetect" {
        Write-Host "Auto-detecting relationships based on naming conventions..." -ForegroundColor Cyan
        $relationships = Get-AutoDetectedRelationships -DefinitionPath $conn.definitionPath
        
        Write-Host "Found $($relationships.Count) potential relationships" -ForegroundColor Cyan
        
        foreach ($rel in $relationships) {
            Write-Host "  [AUTO] $($rel.fromTable).$($rel.fromColumn) -> $($rel.toTable).$($rel.toColumn)" -ForegroundColor Gray
        }
        
        return $relationships
    }
    
    "List" {
        $relDir = "$($conn.definitionPath)\relationships"
        if (Test-Path $relDir) {
            $rels = Get-ChildItem $relDir -Filter "*.tmdl"
            Write-Host "Relationships in model:" -ForegroundColor Cyan
            $rels | ForEach-Object { 
                $content = Get-Content $_.FullName -Raw
                $fromMatch = [regex]::Match($content, 'fromColumn:\s*(\S+)')
                $toMatch = [regex]::Match($content, 'toColumn:\s*(\S+)')
                if ($fromMatch.Success -and $toMatch.Success) {
                    Write-Host "  $($fromMatch.Groups[1].Value) -> $($toMatch.Groups[1].Value)" -ForegroundColor Gray
                }
            }
        } else {
            Write-Host "No relationships directory found" -ForegroundColor Yellow
        }
    }
    
    default {
        Write-Host "Operation '$Operation' not yet implemented" -ForegroundColor Yellow
        Write-Host "Available: CreateFromFactsheet, AutoDetect, List" -ForegroundColor Gray
    }
}
